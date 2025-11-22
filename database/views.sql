-- ============================================
-- ПРЕДСТАВЛЕНИЯ (Views)
-- ============================================

-- 1. Статистика пользователей
CREATE OR REPLACE VIEW v_user_statistics AS
SELECT 
    u.id,
    u.username,
    u.email,
    u.role,
    u.registration_date,
    u.last_login,
    u.is_active,
    up.post_count,
    up.last_activity,
    ur.name as rank_name,
    urp.current_points as rank_points,
    urp.progress_percentage as rank_progress,
    COUNT(DISTINCT t.id) as topics_created,
    COUNT(DISTINCT ua.achievement_id) as achievements_count,
    COALESCE(SUM(p.like_count), 0) as total_likes_received,
    COALESCE(SUM(p.dislike_count), 0) as total_dislikes_received
FROM "GadukaGang_user" u
LEFT JOIN "GadukaGang_userprofile" up ON u.id = up.user_id
LEFT JOIN "GadukaGang_userrankprogress" urp ON u.id = urp.user_id
LEFT JOIN "GadukaGang_userrank" ur ON urp.rank_id = ur.id
LEFT JOIN "GadukaGang_topic" t ON u.id = t.author_id
LEFT JOIN "GadukaGang_post" p ON u.id = p.author_id AND p.is_deleted = FALSE
LEFT JOIN "GadukaGang_userachievement" ua ON u.id = ua.user_id
GROUP BY u.id, u.username, u.email, u.role, u.registration_date, u.last_login, 
         u.is_active, up.post_count, up.last_activity, ur.name, 
         urp.current_points, urp.progress_percentage;

-- 2. Статистика тем
CREATE OR REPLACE VIEW v_topic_statistics AS
SELECT 
    t.id,
    t.title,
    t.created_date,
    t.last_post_date,
    t.is_pinned,
    t.view_count,
    t.average_rating,
    t.rating_count,
    s.name as section_name,
    s.id as section_id,
    u.username as author_username,
    u.id as author_id,
    COUNT(DISTINCT p.id) as posts_count,
    COUNT(DISTINCT p.author_id) as unique_authors,
    COUNT(DISTINCT tt.tag_id) as tags_count,
    MAX(p.created_date) as last_post_created,
    EXTRACT(EPOCH FROM (CURRENT_TIMESTAMP - t.created_date))/86400 as age_days
FROM "GadukaGang_topic" t
JOIN "GadukaGang_section" s ON t.section_id = s.id
JOIN "GadukaGang_user" u ON t.author_id = u.id
LEFT JOIN "GadukaGang_post" p ON t.id = p.topic_id AND p.is_deleted = FALSE
LEFT JOIN "GadukaGang_topictag" tt ON t.id = tt.topic_id
GROUP BY t.id, t.title, t.created_date, t.last_post_date, t.is_pinned, 
         t.view_count, t.average_rating, t.rating_count, s.name, s.id, 
         u.username, u.id;

-- 3. Активные пользователи (последние 24 часа)
CREATE OR REPLACE VIEW v_active_users_24h AS
SELECT 
    u.id,
    u.username,
    u.role,
    up.last_activity,
    up.post_count,
    COUNT(DISTINCT p.id) as posts_last_24h,
    COUNT(DISTINCT t.id) as topics_last_24h
FROM "GadukaGang_user" u
JOIN "GadukaGang_userprofile" up ON u.id = up.user_id
LEFT JOIN "GadukaGang_post" p ON u.id = p.author_id 
    AND p.created_date >= CURRENT_TIMESTAMP - INTERVAL '24 hours'
    AND p.is_deleted = FALSE
LEFT JOIN "GadukaGang_topic" t ON u.id = t.author_id 
    AND t.created_date >= CURRENT_TIMESTAMP - INTERVAL '24 hours'
WHERE up.last_activity >= CURRENT_TIMESTAMP - INTERVAL '24 hours'
GROUP BY u.id, u.username, u.role, up.last_activity, up.post_count
ORDER BY up.last_activity DESC;

-- 4. Статистика по разделам
CREATE OR REPLACE VIEW v_section_statistics AS
SELECT 
    s.id,
    s.name,
    s.description,
    s.created_date,
    u.username as created_by_username,
    COUNT(DISTINCT t.id) as topics_count,
    COUNT(DISTINCT p.id) as posts_count,
    COUNT(DISTINCT t.author_id) as unique_authors,
    MAX(t.created_date) as last_topic_date,
    MAX(p.created_date) as last_post_date,
    COALESCE(AVG(t.view_count), 0) as avg_topic_views,
    COALESCE(AVG(t.average_rating), 0) as avg_topic_rating
FROM "GadukaGang_section" s
LEFT JOIN "GadukaGang_user" u ON s.created_by_id = u.id
LEFT JOIN "GadukaGang_topic" t ON s.id = t.section_id
LEFT JOIN "GadukaGang_post" p ON t.id = p.topic_id AND p.is_deleted = FALSE
GROUP BY s.id, s.name, s.description, s.created_date, u.username;

-- 5. Топ авторов
CREATE OR REPLACE VIEW v_top_contributors AS
SELECT 
    u.id,
    u.username,
    u.role,
    up.post_count,
    COUNT(DISTINCT t.id) as topics_count,
    COALESCE(SUM(p.like_count), 0) as total_likes,
    COALESCE(SUM(p.dislike_count), 0) as total_dislikes,
    COUNT(DISTINCT ua.achievement_id) as achievements_count,
    ur.name as rank_name,
    RANK() OVER (ORDER BY up.post_count DESC) as post_rank
FROM "GadukaGang_user" u
JOIN "GadukaGang_userprofile" up ON u.id = up.user_id
LEFT JOIN "GadukaGang_topic" t ON u.id = t.author_id
LEFT JOIN "GadukaGang_post" p ON u.id = p.author_id AND p.is_deleted = FALSE
LEFT JOIN "GadukaGang_userachievement" ua ON u.id = ua.user_id
LEFT JOIN "GadukaGang_userrankprogress" urp ON u.id = urp.user_id
LEFT JOIN "GadukaGang_userrank" ur ON urp.rank_id = ur.id
WHERE u.is_active = TRUE
GROUP BY u.id, u.username, u.role, up.post_count, ur.name
ORDER BY up.post_count DESC;

-- 6. Активность по дням
CREATE OR REPLACE VIEW v_daily_activity AS
SELECT 
    DATE(created_date) as activity_date,
    COUNT(DISTINCT CASE WHEN table_name = 'user' THEN id END) as new_users,
    COUNT(DISTINCT CASE WHEN table_name = 'topic' THEN id END) as new_topics,
    COUNT(DISTINCT CASE WHEN table_name = 'post' THEN id END) as new_posts,
    COUNT(DISTINCT CASE WHEN table_name = 'post' THEN author_id END) as active_users
FROM (
    SELECT id, author_id, created_date, 'topic' as table_name 
    FROM "GadukaGang_topic"
    UNION ALL
    SELECT id, author_id, created_date, 'post' as table_name 
    FROM "GadukaGang_post" WHERE is_deleted = FALSE
    UNION ALL
    SELECT id, id as author_id, registration_date as created_date, 'user' as table_name 
    FROM "GadukaGang_user"
) combined
WHERE created_date >= CURRENT_TIMESTAMP - INTERVAL '30 days'
GROUP BY DATE(created_date)
ORDER BY activity_date DESC;

-- 7. Популярные теги
CREATE OR REPLACE VIEW v_popular_tags AS
SELECT 
    tg.id,
    tg.name,
    tg.color,
    COUNT(DISTINCT tt.topic_id) as topics_count,
    COUNT(DISTINCT t.author_id) as unique_authors,
    COALESCE(SUM(t.view_count), 0) as total_views,
    COALESCE(AVG(t.average_rating), 0) as avg_rating,
    MAX(t.created_date) as last_used_date
FROM "GadukaGang_tag" tg
LEFT JOIN "GadukaGang_topictag" tt ON tg.id = tt.tag_id
LEFT JOIN "GadukaGang_topic" t ON tt.topic_id = t.id
GROUP BY tg.id, tg.name, tg.color
ORDER BY topics_count DESC;

-- 8. Статистика модерации
CREATE OR REPLACE VIEW v_moderation_statistics AS
SELECT 
    u.id as moderator_id,
    u.username as moderator_username,
    u.role,
    COUNT(DISTINCT ma.id) as total_actions,
    COUNT(DISTINCT CASE WHEN ma.action_type = 'delete_post' THEN ma.id END) as posts_deleted,
    COUNT(DISTINCT CASE WHEN ma.action_type = 'delete_topic' THEN ma.id END) as topics_deleted,
    COUNT(DISTINCT CASE WHEN ma.action_type = 'block_user' THEN ma.id END) as users_blocked,
    COUNT(DISTINCT CASE WHEN ma.action_type = 'process_complaint' THEN ma.id END) as complaints_processed,
    MIN(ma.created_date) as first_action_date,
    MAX(ma.created_date) as last_action_date,
    COUNT(DISTINCT DATE(ma.created_date)) as active_days
FROM "GadukaGang_user" u
LEFT JOIN "GadukaGang_moderatoraction" ma ON u.id = ma.moderator_id
WHERE u.role IN ('moderator', 'admin_level_1', 'admin_level_2', 'admin_level_3', 'super_admin')
GROUP BY u.id, u.username, u.role
ORDER BY total_actions DESC;

-- 9. Жалобы в ожидании
CREATE OR REPLACE VIEW v_pending_complaints AS
SELECT 
    c.id,
    c.target_type,
    c.target_id,
    c.reason,
    c.description,
    c.status,
    c.created_date,
    reporter.username as reporter_username,
    reporter.id as reporter_id,
    moderator.username as assigned_moderator_username,
    moderator.id as assigned_moderator_id,
    EXTRACT(EPOCH FROM (CURRENT_TIMESTAMP - c.created_date))/3600 as hours_pending
FROM "GadukaGang_complaint" c
JOIN "GadukaGang_user" reporter ON c.reporter_id = reporter.id
LEFT JOIN "GadukaGang_user" moderator ON c.assigned_moderator_id = moderator.id
WHERE c.status IN ('open', 'in_review')
ORDER BY c.created_date ASC;

-- 10. Системная активность (логи)
CREATE OR REPLACE VIEW v_system_activity AS
SELECT 
    sl.id,
    sl.action_type,
    sl.action_level,
    sl.description,
    sl.affected_resource_type,
    sl.affected_resource_id,
    sl.timestamp,
    u.username,
    u.role,
    DATE(sl.timestamp) as activity_date,
    EXTRACT(HOUR FROM sl.timestamp) as activity_hour
FROM "GadukaGang_systemlog" sl
LEFT JOIN "GadukaGang_user" u ON sl.user_id = u.id
ORDER BY sl.timestamp DESC;
