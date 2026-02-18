-- Gaduka Gang Forum Database Schema
-- PostgreSQL Script

-- Enable necessary extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Create custom ENUM types
CREATE TYPE user_role_enum AS ENUM ('user', 'moderator', 'admin_level_1', 'admin_level_2', 'admin_level_3', 'super_admin');
CREATE TYPE chat_type_enum AS ENUM ('private', 'group', 'support');
CREATE TYPE complaint_status_enum AS ENUM ('open', 'in_review', 'resolved', 'dismissed');
CREATE TYPE resource_type_enum AS ENUM ('post', 'topic', 'user', 'chat_message');

-- 1. Users table
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    registration_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_login TIMESTAMP,
    is_active BOOLEAN DEFAULT TRUE,
    role user_role_enum DEFAULT 'user'
);

-- 2. User profiles table
CREATE TABLE user_profiles (
    user_id INTEGER PRIMARY KEY REFERENCES users(id) ON DELETE CASCADE,
    avatar_url VARCHAR(500),
    bio TEXT,
    signature TEXT,
    post_count INTEGER DEFAULT 0,
    join_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_activity TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 3. Sections table
CREATE TABLE sections (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    created_by INTEGER REFERENCES users(id),
    created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 4. Topics table
CREATE TABLE topics (
    id SERIAL PRIMARY KEY,
    section_id INTEGER NOT NULL REFERENCES sections(id) ON DELETE CASCADE,
    title VARCHAR(255) NOT NULL,
    author_id INTEGER NOT NULL REFERENCES users(id),
    created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_post_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_pinned BOOLEAN DEFAULT FALSE,
    view_count INTEGER DEFAULT 0
);

-- 5. Posts table
CREATE TABLE posts (
    id SERIAL PRIMARY KEY,
    topic_id INTEGER NOT NULL REFERENCES topics(id) ON DELETE CASCADE,
    author_id INTEGER NOT NULL REFERENCES users(id),
    content TEXT NOT NULL,
    created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_edited_date TIMESTAMP,
    edit_count INTEGER DEFAULT 0,
    is_deleted BOOLEAN DEFAULT FALSE
);

-- 6. Achievements table
CREATE TABLE achievements (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    icon_url VARCHAR(500),
    criteria JSONB
);

-- 7. User achievements table
CREATE TABLE user_achievements (
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    achievement_id INTEGER REFERENCES achievements(id) ON DELETE CASCADE,
    earned_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    awarded_by INTEGER REFERENCES users(id),
    PRIMARY KEY (user_id, achievement_id)
);

-- 8. User ranks table
CREATE TABLE user_ranks (
    id SERIAL PRIMARY KEY,
    name VARCHAR(50) NOT NULL,
    required_points INTEGER NOT NULL,
    icon_url VARCHAR(500)
);

-- 9. User rank progress table
CREATE TABLE user_rank_progress (
    user_id INTEGER PRIMARY KEY REFERENCES users(id) ON DELETE CASCADE,
    rank_id INTEGER REFERENCES user_ranks(id),
    current_points INTEGER DEFAULT 0,
    progress_percentage INTEGER DEFAULT 0
);

-- 10. Tags table
CREATE TABLE tags (
    id SERIAL PRIMARY KEY,
    name VARCHAR(50) UNIQUE NOT NULL,
    color VARCHAR(7) DEFAULT '#000000'
);

-- 11. Topic tags table
CREATE TABLE topic_tags (
    topic_id INTEGER REFERENCES topics(id) ON DELETE CASCADE,
    tag_id INTEGER REFERENCES tags(id) ON DELETE CASCADE,
    PRIMARY KEY (topic_id, tag_id)
);

-- 12. Certificates table
CREATE TABLE certificates (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    template_url VARCHAR(500),
    criteria JSONB
);

-- 13. User certificates table
CREATE TABLE user_certificates (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    certificate_id INTEGER NOT NULL REFERENCES certificates(id),
    awarded_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    awarded_by INTEGER REFERENCES users(id),
    expiration_date TIMESTAMP
);

-- 14. Complaints table
CREATE TABLE complaints (
    id SERIAL PRIMARY KEY,
    reporter_id INTEGER NOT NULL REFERENCES users(id),
    target_type resource_type_enum NOT NULL,
    target_id INTEGER NOT NULL,
    reason VARCHAR(100),
    description TEXT,
    status complaint_status_enum DEFAULT 'open',
    assigned_moderator INTEGER REFERENCES users(id),
    created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    resolved_date TIMESTAMP
);

-- 15. Chats table
CREATE TABLE chats (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100),
    chat_type chat_type_enum NOT NULL,
    created_by INTEGER REFERENCES users(id),
    created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_active BOOLEAN DEFAULT TRUE
);

-- 16. Chat participants table
CREATE TABLE chat_participants (
    chat_id INTEGER REFERENCES chats(id) ON DELETE CASCADE,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    joined_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    left_date TIMESTAMP,
    role_in_chat VARCHAR(20) DEFAULT 'member',
    PRIMARY KEY (chat_id, user_id)
);

-- 17. Chat messages table
CREATE TABLE chat_messages (
    id SERIAL PRIMARY KEY,
    chat_id INTEGER NOT NULL REFERENCES chats(id) ON DELETE CASCADE,
    sender_id INTEGER NOT NULL REFERENCES users(id),
    content TEXT NOT NULL,
    sent_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_edited BOOLEAN DEFAULT FALSE,
    edited_date TIMESTAMP,
    is_deleted BOOLEAN DEFAULT FALSE
);

-- 18. System logs table
CREATE TABLE system_logs (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    action_type VARCHAR(50) NOT NULL,
    action_level user_role_enum NOT NULL,
    description TEXT,
    affected_resource_type VARCHAR(50),
    affected_resource_id INTEGER,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 19. Forum settings table
CREATE TABLE forum_settings (
    id SERIAL PRIMARY KEY,
    setting_name VARCHAR(100) UNIQUE NOT NULL,
    setting_value JSONB,
    category VARCHAR(50),
    last_modified TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    modified_by INTEGER REFERENCES users(id)
);

-- Create indexes for better performance
CREATE INDEX idx_users_username ON users(username);
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_topics_section ON topics(section_id);
CREATE INDEX idx_topics_author ON topics(author_id);
CREATE INDEX idx_posts_topic ON posts(topic_id);
CREATE INDEX idx_posts_author ON posts(author_id);
CREATE INDEX idx_posts_created ON posts(created_date);
CREATE INDEX idx_complaints_status ON complaints(status);
CREATE INDEX idx_complaints_moderator ON complaints(assigned_moderator);
CREATE INDEX idx_chat_messages_chat ON chat_messages(chat_id);
CREATE INDEX idx_chat_messages_sender ON chat_messages(sender_id);
CREATE INDEX idx_system_logs_user ON system_logs(user_id);
CREATE INDEX idx_system_logs_timestamp ON system_logs(timestamp);

-- TRIGGERS

-- Trigger function to update user post count
CREATE OR REPLACE FUNCTION update_user_post_count()
RETURNS TRIGGER AS $$
BEGIN
    IF (TG_OP = 'INSERT') THEN
        UPDATE user_profiles 
        SET post_count = post_count + 1,
            last_activity = CURRENT_TIMESTAMP
        WHERE user_id = NEW.author_id;
        RETURN NEW;
    ELSIF (TG_OP = 'DELETE') THEN
        UPDATE user_profiles 
        SET post_count = post_count - 1
        WHERE user_id = OLD.author_id;
        RETURN OLD;
    END IF;
    RETURN NULL;
END;
$$ LANGUAGE plpgsql;

-- Trigger to update user post count on post insert/delete
CREATE TRIGGER trigger_update_user_post_count
AFTER INSERT OR DELETE ON posts
FOR EACH ROW
EXECUTE FUNCTION update_user_post_count();

-- Trigger function to update topic last post date
CREATE OR REPLACE FUNCTION update_topic_last_post_date()
RETURNS TRIGGER AS $$
BEGIN
    IF (TG_OP = 'INSERT') THEN
        UPDATE topics 
        SET last_post_date = NEW.created_date 
        WHERE id = NEW.topic_id;
        RETURN NEW;
    END IF;
    RETURN NULL;
END;
$$ LANGUAGE plpgsql;

-- Trigger to update topic last post date on post insert
CREATE TRIGGER trigger_update_topic_last_post_date
AFTER INSERT ON posts
FOR EACH ROW
EXECUTE FUNCTION update_topic_last_post_date();

-- FUNCTIONS

-- Function to check user permission level
CREATE OR REPLACE FUNCTION check_user_permission(p_user_id INTEGER, required_role user_role_enum)
RETURNS BOOLEAN AS $$
DECLARE
    user_role user_role_enum;
    role_hierarchy INTEGER;
    required_hierarchy INTEGER;
BEGIN
    SELECT role INTO user_role FROM users WHERE id = p_user_id;
    
    -- Define role hierarchy (higher number = higher privilege)
    CASE user_role
        WHEN 'user' THEN role_hierarchy := 1;
        WHEN 'moderator' THEN role_hierarchy := 2;
        WHEN 'admin_level_1' THEN role_hierarchy := 3;
        WHEN 'admin_level_2' THEN role_hierarchy := 4;
        WHEN 'admin_level_3' THEN role_hierarchy := 5;
        WHEN 'super_admin' THEN role_hierarchy := 6;
        ELSE role_hierarchy := 1;
    END CASE;
    
    CASE required_role
        WHEN 'user' THEN required_hierarchy := 1;
        WHEN 'moderator' THEN required_hierarchy := 2;
        WHEN 'admin_level_1' THEN required_hierarchy := 3;
        WHEN 'admin_level_2' THEN required_hierarchy := 4;
        WHEN 'admin_level_3' THEN required_hierarchy := 5;
        WHEN 'super_admin' THEN required_hierarchy := 6;
        ELSE required_hierarchy := 1;
    END CASE;
    
    RETURN role_hierarchy >= required_hierarchy;
END;
$$ LANGUAGE plpgsql;

-- Function to calculate rank progress
CREATE OR REPLACE FUNCTION calculate_rank_progress(p_user_id INTEGER)
RETURNS INTEGER AS $$
DECLARE
    current_points INTEGER;
    required_points INTEGER;
    next_rank_points INTEGER;
    progress INTEGER;
BEGIN
    SELECT current_points INTO current_points 
    FROM user_rank_progress 
    WHERE user_id = p_user_id;
    
    -- Get the points required for the next rank
    SELECT MIN(required_points) INTO next_rank_points
    FROM user_ranks 
    WHERE required_points > current_points;
    
    -- If there's no next rank, return 100%
    IF next_rank_points IS NULL THEN
        RETURN 100;
    END IF;
    
    -- Calculate progress percentage
    progress := (current_points * 100) / next_rank_points;
    
    RETURN progress;
END;
$$ LANGUAGE plpgsql;

-- Function to search topics by tags
CREATE OR REPLACE FUNCTION search_topics_by_tags(tag_names TEXT[])
RETURNS TABLE(topic_id INTEGER) AS $$
BEGIN
    RETURN QUERY
    SELECT DISTINCT t.id
    FROM topics t
    JOIN topic_tags tt ON t.id = tt.topic_id
    JOIN tags tg ON tt.tag_id = tg.id
    WHERE tg.name = ANY(tag_names);
END;
$$ LANGUAGE plpgsql;

-- STORED PROCEDURES (Functions in PostgreSQL)

-- Procedure to create a new user with profile
CREATE OR REPLACE FUNCTION create_new_user(
    p_username VARCHAR(50),
    p_email VARCHAR(255),
    p_password_hash VARCHAR(255)
) RETURNS INTEGER AS $$
DECLARE
    new_user_id INTEGER;
BEGIN
    -- Create the user
    INSERT INTO users (username, email, password_hash, registration_date)
    VALUES (p_username, p_email, p_password_hash, CURRENT_TIMESTAMP)
    RETURNING id INTO new_user_id;
    
    -- Create user profile
    INSERT INTO user_profiles (user_id, post_count, join_date, last_activity)
    VALUES (new_user_id, 0, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP);
    
    -- Initialize rank progress
    INSERT INTO user_rank_progress (user_id, rank_id, current_points, progress_percentage)
    VALUES (new_user_id, 1, 0, 0);
    
    RETURN new_user_id;
END;
$$ LANGUAGE plpgsql;

-- Procedure to award achievement to user
CREATE OR REPLACE FUNCTION award_achievement(
    p_user_id INTEGER,
    p_achievement_id INTEGER,
    p_awarded_by INTEGER
) RETURNS BOOLEAN AS $$
BEGIN
    -- Check if achievement is already awarded
    IF NOT EXISTS (
        SELECT 1 FROM user_achievements 
        WHERE user_id = p_user_id AND achievement_id = p_achievement_id
    ) THEN
        -- Award the achievement
        INSERT INTO user_achievements (user_id, achievement_id, earned_date, awarded_by)
        VALUES (p_user_id, p_achievement_id, CURRENT_TIMESTAMP, p_awarded_by);
        
        -- Increase user points for rank progress
        UPDATE user_rank_progress 
        SET current_points = current_points + 10
        WHERE user_id = p_user_id;
        
        RETURN TRUE;
    END IF;
    
    RETURN FALSE;
END;
$$ LANGUAGE plpgsql;

-- Procedure to process a complaint
CREATE OR REPLACE FUNCTION process_complaint(
    p_complaint_id INTEGER,
    p_moderator_id INTEGER,
    p_resolution complaint_status_enum,
    p_notes TEXT
) RETURNS VOID AS $$
BEGIN
    -- Update complaint status
    UPDATE complaints 
    SET status = p_resolution,
        assigned_moderator = p_moderator_id,
        resolved_date = CURRENT_TIMESTAMP
    WHERE id = p_complaint_id;
    
    -- Log the action
    INSERT INTO system_logs (
        user_id, 
        action_type, 
        action_level, 
        description, 
        affected_resource_type, 
        affected_resource_id, 
        timestamp
    )
    VALUES (
        p_moderator_id, 
        'moderator_action', 
        'moderator', 
        'Processed complaint #' || p_complaint_id || ' with resolution: ' || p_resolution || '. Notes: ' || COALESCE(p_notes, ''),
        'complaint',
        p_complaint_id,
        CURRENT_TIMESTAMP
    );
END;
$$ LANGUAGE plpgsql;

-- Procedure to create backup log entry
CREATE OR REPLACE FUNCTION create_backup_log() RETURNS VOID AS $$
BEGIN
    INSERT INTO system_logs (
        user_id, 
        action_type, 
        action_level, 
        description, 
        timestamp
    )
    VALUES (
        NULL, 
        'system_action', 
        'super_admin', 
        'Backup created at ' || CURRENT_TIMESTAMP,
        CURRENT_TIMESTAMP
    );
END;
$$ LANGUAGE plpgsql;

-- VIEW for user statistics
CREATE VIEW user_statistics AS
SELECT 
    u.id,
    u.username,
    u.registration_date,
    up.post_count,
    up.last_activity,
    urp.current_points,
    ur.name as current_rank
FROM users u
JOIN user_profiles up ON u.id = up.user_id
JOIN user_rank_progress urp ON u.id = urp.user_id
LEFT JOIN user_ranks ur ON urp.rank_id = ur.id;

-- VIEW for topic statistics
CREATE VIEW topic_statistics AS
SELECT 
    t.id,
    t.title,
    t.created_date,
    t.last_post_date,
    t.view_count,
    COUNT(p.id) as post_count,
    s.name as section_name
FROM topics t
JOIN sections s ON t.section_id = s.id
LEFT JOIN posts p ON t.id = p.topic_id
GROUP BY t.id, t.title, t.created_date, t.last_post_date, t.view_count, s.name;

-- VIEW for active users (last 24 hours)
CREATE VIEW active_users AS
SELECT 
    u.id,
    u.username,
    up.last_activity,
    up.post_count
FROM users u
JOIN user_profiles up ON u.id = up.user_id
WHERE up.last_activity >= CURRENT_TIMESTAMP - INTERVAL '24 hours'
ORDER BY up.last_activity DESC;

-- Insert initial data for testing

-- Insert default ranks
INSERT INTO user_ranks (name, required_points, icon_url) VALUES 
('Новичок', 0, '/static/images/ranks/beginner.png'),
('Участник', 50, '/static/images/ranks/member.png'),
('Эксперт', 200, '/static/images/ranks/expert.png'),
('Мастер', 500, '/static/images/ranks/master.png'),
('Гуру', 1000, '/static/images/ranks/guru.png');

-- Insert default sections
INSERT INTO sections (name, description, created_by) VALUES 
('Общие вопросы Python', 'Общие вопросы и обсуждения о языке Python', NULL),
('Проблемы и ошибки', 'Обсуждение ошибок и проблем в коде', NULL),
('Библиотеки и фреймворки', 'Обсуждение популярных библиотек и фреймворков', NULL),
('Искусственный интеллект и машинное обучение', 'Обсуждение AI и ML технологий', NULL),
('Веб-разработка', 'Вопросы веб-разработки на Python', NULL),
('Автоматизация и скрипты', 'Создание скриптов и автоматизация задач', NULL);

-- Insert default tags
INSERT INTO tags (name, color) VALUES 
('python', '#3572A5'),
('django', '#092E20'),
('flask', '#E3242B'),
('fastapi', '#009688'),
('async', '#FFD43B'),
('oop', '#6A5ACD'),
('database', '#4EA94B'),
('ai', '#FF6B6B'),
('ml', '#4ECDC4');

-- Insert sample achievements
INSERT INTO achievements (name, description, icon_url, criteria) VALUES 
('Первое сообщение', 'Написать первое сообщение на форуме', '/static/images/achievements/first-post.png', '{"type": "post_count", "value": 1}'),
('Активный участник', 'Написать 50 сообщений', '/static/images/achievements/active.png', '{"type": "post_count", "value": 50}'),
('Эксперт по Python', 'Получить 100 положительных оценок', '/static/images/achievements/python-expert.png', '{"type": "upvotes", "value": 100}'),
('Помощник', 'Помочь 20 пользователям', '/static/images/achievements/helper.png', '{"type": "helped_users", "value": 20}');

-- Insert forum settings
INSERT INTO forum_settings (setting_name, setting_value, category, modified_by) VALUES 
('forum_name', '"Gaduka Gang"', 'general', NULL),
('posts_per_page', '20', 'display', NULL),
('topics_per_page', '30', 'display', NULL),
('max_signature_length', '200', 'user', NULL),
('allow_user_registration', 'true', 'security', NULL);

-- Grant permissions (adjust as needed for your setup)
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO CURRENT_USER;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO CURRENT_USER;



-- -- Создание пользователя (если еще не создан)
-- CREATE USER forum_owner WITH PASSWORD '1111';

-- -- Предоставление прав на базу данных
-- GRANT ALL PRIVILEGES ON DATABASE forum_database TO forum_owner;

-- -- Подключение к базе данных forum_database (выполняется в pgAdmin через подключение к этой БД)
-- -- Предоставление прав на схему public
-- GRANT ALL ON SCHEMA public TO forum_owner;

-- -- Предоставление прав на все существующие таблицы в схеме public
-- GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO forum_owner;

-- -- Предоставление прав на все существующие последовательности в схеме public
-- GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO forum_owner;

-- -- Установка прав по умолчанию для новых таблиц и последовательностей
-- ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO forum_owner;
-- ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON SEQUENCES TO forum_owner;

-- -- Если нужно сделать пользователя владельцем всех таблиц (опционально)
-- -- Это изменит владельца всех таблиц на forum_owner
-- DO $$ 
-- DECLARE 
--     r record;
-- BEGIN
--     FOR r IN (SELECT tablename FROM pg_tables WHERE schemaname = 'public') 
--     LOOP
--         EXECUTE 'ALTER TABLE ' || quote_ident(r.tablename) || ' OWNER TO forum_owner';
--     END LOOP;
-- END $$;

-- -- Проверка прав пользователя
-- SELECT r.rolname, r.rolsuper, r.rolinherit,
--        r.rolcreaterole, r.rolcreatedb, r.rolcanlogin,
--        r.rolconnlimit, r.rolvaliduntil,
--        ARRAY(SELECT b.rolname
--              FROM pg_catalog.pg_auth_members m
--              JOIN pg_catalog.pg_roles b ON (m.roleid = b.oid)
--              WHERE m.member = r.oid) as memberof
-- FROM pg_catalog.pg_roles r
-- WHERE r.rolname = 'forum_owner';

SELECT * FROM "GadukaGang_systemlog" ORDER BY timestamp DESC LIMIT 10;
