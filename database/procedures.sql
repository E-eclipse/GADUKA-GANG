-- ============================================
-- ХРАНИМЫЕ ПРОЦЕДУРЫ (Stored Procedures)
-- ============================================

-- 1. Расчёт статистики пользователя
CREATE OR REPLACE FUNCTION calculate_user_statistics(p_user_id INTEGER)
RETURNS TABLE(
    total_posts INTEGER,
    total_topics INTEGER,
    total_likes INTEGER,
    total_dislikes INTEGER,
    achievements_count INTEGER,
    rank_name VARCHAR(50),
    rank_progress INTEGER
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        COALESCE(COUNT(DISTINCT p.id), 0)::INTEGER as total_posts,
        COALESCE(COUNT(DISTINCT t.id), 0)::INTEGER as total_topics,
        0::INTEGER as total_likes,
        0::INTEGER as total_dislikes,
        COALESCE(COUNT(DISTINCT ua.achievement_id), 0)::INTEGER as achievements_count,
        COALESCE(ur.name, 'Новичок')::VARCHAR(50) as rank_name,
        COALESCE(urp.progress_percentage, 0)::INTEGER as rank_progress
    FROM users u
    LEFT JOIN user_profiles up ON u.id = up.user_id
    LEFT JOIN posts p ON u.id = p.author_id AND p.is_deleted = FALSE
    LEFT JOIN topics t ON u.id = t.author_id
    LEFT JOIN user_achievements ua ON u.id = ua.user_id
    LEFT JOIN user_rank_progress urp ON u.id = urp.user_id
    LEFT JOIN user_ranks ur ON urp.rank_id = ur.id
    WHERE u.id = p_user_id
    GROUP BY ur.name, urp.progress_percentage;
END;
$$ LANGUAGE plpgsql;

-- 2. Пакетный пересчёт рейтингов тем
CREATE OR REPLACE FUNCTION batch_update_topic_ratings()
RETURNS TABLE(
    updated_count INTEGER,
    execution_time INTERVAL
) AS $$
DECLARE
    start_time TIMESTAMP;
    end_time TIMESTAMP;
    affected_rows INTEGER;
BEGIN
    start_time := clock_timestamp();
    
    -- Обновление рейтингов тем (упрощено, так как таблица topicrating отсутствует в схеме)
    -- В реальной схеме нет таблицы topicrating, поэтому эта функция не будет обновлять рейтинги
    -- Оставляем пустую операцию для совместимости
    affected_rows := 0;
    
    GET DIAGNOSTICS affected_rows = ROW_COUNT;
    end_time := clock_timestamp();
    
    RETURN QUERY SELECT affected_rows, (end_time - start_time);
END;
$$ LANGUAGE plpgsql;

-- 3. Архивация старых постов
CREATE OR REPLACE FUNCTION archive_old_posts(p_days_threshold INTEGER DEFAULT 365)
RETURNS TABLE(
    archived_count INTEGER,
    oldest_post_date TIMESTAMP
) AS $$
DECLARE
    cutoff_date TIMESTAMP;
    affected_rows INTEGER;
    oldest_date TIMESTAMP;
BEGIN
    cutoff_date := CURRENT_TIMESTAMP - (p_days_threshold || ' days')::INTERVAL;
    
    -- Помечаем старые посты как удалённые (мягкое удаление)
    UPDATE posts
    SET is_deleted = TRUE
    WHERE created_date < cutoff_date 
      AND is_deleted = FALSE
      AND edit_count = 0; -- Не архивируем редактированные посты
    
    GET DIAGNOSTICS affected_rows = ROW_COUNT;
    
    -- Получаем дату самого старого поста
    SELECT MIN(created_date) INTO oldest_date
    FROM posts
    WHERE is_deleted = TRUE;
    
    RETURN QUERY SELECT affected_rows, oldest_date;
END;
$$ LANGUAGE plpgsql;

-- 4. Генерация аналитического отчёта
CREATE OR REPLACE FUNCTION generate_analytics_report(
    p_date_from TIMESTAMP DEFAULT NULL,
    p_date_to TIMESTAMP DEFAULT NULL
)
RETURNS TABLE(
    metric_name VARCHAR(100),
    metric_value NUMERIC,
    metric_change_percent NUMERIC
) AS $$
DECLARE
    v_date_from TIMESTAMP;
    v_date_to TIMESTAMP;
    v_prev_period_from TIMESTAMP;
    v_prev_period_to TIMESTAMP;
BEGIN
    -- Устанавливаем даты по умолчанию (последние 30 дней)
    v_date_to := COALESCE(p_date_to, CURRENT_TIMESTAMP);
    v_date_from := COALESCE(p_date_from, v_date_to - INTERVAL '30 days');
    
    -- Вычисляем предыдущий период для сравнения
    v_prev_period_to := v_date_from;
    v_prev_period_from := v_prev_period_to - (v_date_to - v_date_from);
    
    RETURN QUERY
    WITH 
    -- Новые пользователи
    current_users AS (
        SELECT COUNT(*) as cnt FROM users 
        WHERE registration_date BETWEEN v_date_from AND v_date_to
    ),
    prev_users AS (
        SELECT COUNT(*) as cnt FROM users 
        WHERE registration_date BETWEEN v_prev_period_from AND v_prev_period_to
    ),
    -- Новые темы
    current_topics AS (
        SELECT COUNT(*) as cnt FROM topics 
        WHERE created_date BETWEEN v_date_from AND v_date_to
    ),
    prev_topics AS (
        SELECT COUNT(*) as cnt FROM topics 
        WHERE created_date BETWEEN v_prev_period_from AND v_prev_period_to
    ),
    -- Новые посты
    current_posts AS (
        SELECT COUNT(*) as cnt FROM posts 
        WHERE created_date BETWEEN v_date_from AND v_date_to AND is_deleted = FALSE
    ),
    prev_posts AS (
        SELECT COUNT(*) as cnt FROM posts 
        WHERE created_date BETWEEN v_prev_period_from AND v_prev_period_to AND is_deleted = FALSE
    ),
    -- Активные пользователи
    current_active AS (
        SELECT COUNT(DISTINCT author_id) as cnt FROM posts 
        WHERE created_date BETWEEN v_date_from AND v_date_to AND is_deleted = FALSE
    ),
    prev_active AS (
        SELECT COUNT(DISTINCT author_id) as cnt FROM posts 
        WHERE created_date BETWEEN v_prev_period_from AND v_prev_period_to AND is_deleted = FALSE
    )
    SELECT 
        'Новые пользователи'::VARCHAR(100),
        cu.cnt::NUMERIC,
        CASE WHEN pu.cnt > 0 THEN ((cu.cnt - pu.cnt)::NUMERIC / pu.cnt * 100) ELSE 0 END
    FROM current_users cu, prev_users pu
    
    UNION ALL
    
    SELECT 
        'Новые темы'::VARCHAR(100),
        ct.cnt::NUMERIC,
        CASE WHEN pt.cnt > 0 THEN ((ct.cnt - pt.cnt)::NUMERIC / pt.cnt * 100) ELSE 0 END
    FROM current_topics ct, prev_topics pt
    
    UNION ALL
    
    SELECT 
        'Новые посты'::VARCHAR(100),
        cp.cnt::NUMERIC,
        CASE WHEN pp.cnt > 0 THEN ((cp.cnt - pp.cnt)::NUMERIC / pp.cnt * 100) ELSE 0 END
    FROM current_posts cp, prev_posts pp
    
    UNION ALL
    
    SELECT 
        'Активные пользователи'::VARCHAR(100),
        ca.cnt::NUMERIC,
        CASE WHEN pa.cnt > 0 THEN ((ca.cnt - pa.cnt)::NUMERIC / pa.cnt * 100) ELSE 0 END
    FROM current_active ca, prev_active pa;
END;
$$ LANGUAGE plpgsql;

-- 5. Массовая выдача достижений
CREATE OR REPLACE FUNCTION award_achievements_batch()
RETURNS TABLE(
    user_id INTEGER,
    achievement_id INTEGER,
    achievement_name VARCHAR(100)
) AS $$
BEGIN
    -- Достижение "Первое сообщение" (1 пост)
    INSERT INTO user_achievements (user_id, achievement_id, earned_date, awarded_by)
    SELECT DISTINCT 
        p.author_id,
        a.id,
        CURRENT_TIMESTAMP,
        NULL
    FROM posts p
    JOIN achievements a ON a.name = 'Первое сообщение'
    WHERE p.is_deleted = FALSE
    AND NOT EXISTS (
        SELECT 1 FROM user_achievements ua 
        WHERE ua.user_id = p.author_id AND ua.achievement_id = a.id
    )
    GROUP BY p.author_id, a.id
    HAVING COUNT(p.id) >= 1;
    
    -- Достижение "Активный участник" (50 постов)
    INSERT INTO user_achievements (user_id, achievement_id, earned_date, awarded_by)
    SELECT DISTINCT 
        p.author_id,
        a.id,
        CURRENT_TIMESTAMP,
        NULL
    FROM posts p
    JOIN achievements a ON a.name = 'Активный участник'
    WHERE p.is_deleted = FALSE
    AND NOT EXISTS (
        SELECT 1 FROM user_achievements ua 
        WHERE ua.user_id = p.author_id AND ua.achievement_id = a.id
    )
    GROUP BY p.author_id, a.id
    HAVING COUNT(p.id) >= 50;
    
    -- Возвращаем список выданных достижений
    RETURN QUERY
    SELECT 
        ua.user_id,
        ua.achievement_id,
        a.name
    FROM user_achievements ua
    JOIN achievements a ON ua.achievement_id = a.id
    WHERE ua.earned_date >= CURRENT_TIMESTAMP - INTERVAL '1 minute';
END;
$$ LANGUAGE plpgsql;

-- 6. Обработка жалобы с транзакцией
CREATE OR REPLACE FUNCTION process_complaint_transaction(
    p_complaint_id INTEGER,
    p_moderator_id INTEGER,
    p_new_status VARCHAR(20),
    p_action_description TEXT
)
RETURNS BOOLEAN AS $$
DECLARE
    v_complaint_exists BOOLEAN;
BEGIN
    -- Проверяем существование жалобы
    SELECT EXISTS(
        SELECT 1 FROM complaints WHERE id = p_complaint_id
    ) INTO v_complaint_exists;
    
    IF NOT v_complaint_exists THEN
        RAISE EXCEPTION 'Жалоба с ID % не найдена', p_complaint_id;
    END IF;
    
    -- Начинаем транзакцию
    BEGIN
        -- Обновляем статус жалобы
        UPDATE complaints
        SET 
            status = p_new_status::complaint_status_enum,
            assigned_moderator = p_moderator_id,
            resolved_date = CASE WHEN p_new_status IN ('resolved', 'dismissed') 
                                 THEN CURRENT_TIMESTAMP 
                                 ELSE resolved_date END
        WHERE id = p_complaint_id;
        
        -- Логируем в системный лог (таблица moderatoraction отсутствует в схеме)
        INSERT INTO system_logs (
            user_id,
            action_type,
            action_level,
            description,
            affected_resource_type,
            affected_resource_id,
            timestamp
        ) VALUES (
            p_moderator_id,
            'complaint_processed',
            'moderator'::user_role_enum,
            'Жалоба #' || p_complaint_id || ' обработана: ' || p_new_status || '. ' || COALESCE(p_action_description, ''),
            'complaint',
            p_complaint_id,
            CURRENT_TIMESTAMP
        );
        
        RETURN TRUE;
    EXCEPTION
        WHEN OTHERS THEN
            -- В случае ошибки откатываем транзакцию
            RAISE NOTICE 'Ошибка при обработке жалобы: %', SQLERRM;
            RETURN FALSE;
    END;
END;
$$ LANGUAGE plpgsql;

-- 7. Обновление рангов пользователей
CREATE OR REPLACE FUNCTION update_user_ranks()
RETURNS TABLE(
    user_id INTEGER,
    old_rank VARCHAR(50),
    new_rank VARCHAR(50),
    current_points INTEGER
) AS $$
BEGIN
    RETURN QUERY
    WITH user_points AS (
        SELECT 
            urp.user_id,
            urp.current_points,
            urp.rank_id as old_rank_id,
            (SELECT id FROM user_ranks 
             WHERE required_points <= urp.current_points 
             ORDER BY required_points DESC LIMIT 1) as new_rank_id
        FROM user_rank_progress urp
    ),
    rank_updates AS (
        UPDATE user_rank_progress urp
        SET rank_id = up.new_rank_id
        FROM user_points up
        WHERE urp.user_id = up.user_id 
          AND up.old_rank_id != up.new_rank_id
        RETURNING urp.user_id, up.old_rank_id, up.new_rank_id, urp.current_points
    )
    SELECT 
        ru.user_id,
        COALESCE(old_r.name, 'Нет ранга') as old_rank,
        COALESCE(new_r.name, 'Нет ранга') as new_rank,
        ru.current_points
    FROM rank_updates ru
    LEFT JOIN user_ranks old_r ON ru.old_rank_id = old_r.id
    LEFT JOIN user_ranks new_r ON ru.new_rank_id = new_r.id;
END;
$$ LANGUAGE plpgsql;
