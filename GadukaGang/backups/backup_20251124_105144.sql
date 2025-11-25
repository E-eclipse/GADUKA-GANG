--
-- PostgreSQL database dump
--

-- Dumped from database version 17.2
-- Dumped by pg_dump version 17.2

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET transaction_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

--
-- Name: uuid-ossp; Type: EXTENSION; Schema: -; Owner: -
--

CREATE EXTENSION IF NOT EXISTS "uuid-ossp" WITH SCHEMA public;


--
-- Name: EXTENSION "uuid-ossp"; Type: COMMENT; Schema: -; Owner: -
--

COMMENT ON EXTENSION "uuid-ossp" IS 'generate universally unique identifiers (UUIDs)';


--
-- Name: chat_type_enum; Type: TYPE; Schema: public; Owner: -
--

CREATE TYPE public.chat_type_enum AS ENUM (
    'private',
    'group',
    'support'
);


--
-- Name: complaint_status_enum; Type: TYPE; Schema: public; Owner: -
--

CREATE TYPE public.complaint_status_enum AS ENUM (
    'open',
    'in_review',
    'resolved',
    'dismissed'
);


--
-- Name: resource_type_enum; Type: TYPE; Schema: public; Owner: -
--

CREATE TYPE public.resource_type_enum AS ENUM (
    'post',
    'topic',
    'user',
    'chat_message'
);


--
-- Name: user_role_enum; Type: TYPE; Schema: public; Owner: -
--

CREATE TYPE public.user_role_enum AS ENUM (
    'user',
    'moderator',
    'admin_level_1',
    'admin_level_2',
    'admin_level_3',
    'super_admin'
);


--
-- Name: archive_old_posts(integer); Type: FUNCTION; Schema: public; Owner: -
--

CREATE FUNCTION public.archive_old_posts(p_days_threshold integer DEFAULT 365) RETURNS TABLE(archived_count integer, oldest_post_date timestamp without time zone)
    LANGUAGE plpgsql
    AS $$
DECLARE
    cutoff_date TIMESTAMP;
    affected_rows INTEGER;
    oldest_date TIMESTAMP;
BEGIN
    cutoff_date := CURRENT_TIMESTAMP - (p_days_threshold || ' days')::INTERVAL;
    
    -- Помечаем старые посты как удалённые (мягкое удаление)
    UPDATE "GadukaGang_post"
    SET is_deleted = TRUE
    WHERE created_date < cutoff_date 
      AND is_deleted = FALSE
      AND edit_count = 0; -- Не архивируем редактированные посты
    
    GET DIAGNOSTICS affected_rows = ROW_COUNT;
    
    -- Получаем дату самого старого поста
    SELECT MIN(created_date) INTO oldest_date
    FROM "GadukaGang_post"
    WHERE is_deleted = TRUE;
    
    RETURN QUERY SELECT affected_rows, oldest_date;
END;
$$;


--
-- Name: audit_moderator_actions(); Type: FUNCTION; Schema: public; Owner: -
--

CREATE FUNCTION public.audit_moderator_actions() RETURNS trigger
    LANGUAGE plpgsql
    AS $$
BEGIN
    IF (TG_OP = 'INSERT') THEN
        -- Дополнительное логирование критичных действий
        IF NEW.action_type IN ('delete_post', 'delete_topic', 'block_user') THEN
            INSERT INTO "GadukaGang_systemlog" (
                user_id,
                action_type,
                action_level,
                description,
                affected_resource_type,
                affected_resource_id,
                timestamp
            ) VALUES (
                NEW.moderator_id,
                'critical_moderator_action',
                'moderator',
                'Критичное действие модератора: ' || NEW.action_type || ' - ' || NEW.description,
                NEW.target_type,
                NEW.target_id,
                CURRENT_TIMESTAMP
            );
        END IF;
        RETURN NEW;
    END IF;
    RETURN NULL;
END;
$$;


--
-- Name: audit_post_changes(); Type: FUNCTION; Schema: public; Owner: -
--

CREATE FUNCTION public.audit_post_changes() RETURNS trigger
    LANGUAGE plpgsql
    AS $$
BEGIN
    IF (TG_OP = 'UPDATE') THEN
        -- Логируем редактирование контента
        IF OLD.content != NEW.content THEN
            INSERT INTO "GadukaGang_systemlog" (
                user_id,
                action_type,
                action_level,
                description,
                affected_resource_type,
                affected_resource_id,
                timestamp
            ) VALUES (
                NEW.author_id,
                'post_edited',
                'user',
                'Пост #' || NEW.id || ' отредактирован (редакция #' || NEW.edit_count || ')',
                'post',
                NEW.id,
                CURRENT_TIMESTAMP
            );
        END IF;
        
        -- Логируем удаление
        IF OLD.is_deleted = FALSE AND NEW.is_deleted = TRUE THEN
            INSERT INTO "GadukaGang_systemlog" (
                user_id,
                action_type,
                action_level,
                description,
                affected_resource_type,
                affected_resource_id,
                timestamp
            ) VALUES (
                NEW.author_id,
                'post_deleted',
                'user',
                'Пост #' || NEW.id || ' помечен как удалённый',
                'post',
                NEW.id,
                CURRENT_TIMESTAMP
            );
        END IF;
        
        RETURN NEW;
    END IF;
    RETURN NULL;
END;
$$;


--
-- Name: audit_user_changes(); Type: FUNCTION; Schema: public; Owner: -
--

CREATE FUNCTION public.audit_user_changes() RETURNS trigger
    LANGUAGE plpgsql
    AS $$
BEGIN
    IF (TG_OP = 'UPDATE') THEN
        -- Логируем изменение роли
        IF OLD.role != NEW.role THEN
            INSERT INTO "GadukaGang_systemlog" (
                user_id,
                action_type,
                action_level,
                description,
                affected_resource_type,
                affected_resource_id,
                timestamp
            ) VALUES (
                NEW.id,
                'role_changed',
                NEW.role,
                'Роль изменена с "' || OLD.role || '" на "' || NEW.role || '"',
                'user',
                NEW.id,
                CURRENT_TIMESTAMP
            );
        END IF;
        
        -- Логируем изменение статуса активности
        IF OLD.is_active != NEW.is_active THEN
            INSERT INTO "GadukaGang_systemlog" (
                user_id,
                action_type,
                action_level,
                description,
                affected_resource_type,
                affected_resource_id,
                timestamp
            ) VALUES (
                NEW.id,
                'user_status_changed',
                NEW.role,
                'Статус активности изменён: ' || CASE WHEN NEW.is_active THEN 'активен' ELSE 'неактивен' END,
                'user',
                NEW.id,
                CURRENT_TIMESTAMP
            );
        END IF;
        
        RETURN NEW;
    ELSIF (TG_OP = 'DELETE') THEN
        INSERT INTO "GadukaGang_systemlog" (
            user_id,
            action_type,
            action_level,
            description,
            affected_resource_type,
            affected_resource_id,
            timestamp
        ) VALUES (
            OLD.id,
            'user_deleted',
            OLD.role,
            'Пользователь удалён: ' || OLD.username,
            'user',
            OLD.id,
            CURRENT_TIMESTAMP
        );
        RETURN OLD;
    END IF;
    RETURN NULL;
END;
$$;


--
-- Name: award_achievement(integer, integer, integer); Type: FUNCTION; Schema: public; Owner: -
--

CREATE FUNCTION public.award_achievement(p_user_id integer, p_achievement_id integer, p_awarded_by integer) RETURNS boolean
    LANGUAGE plpgsql
    AS $$
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
$$;


--
-- Name: award_achievements_batch(); Type: FUNCTION; Schema: public; Owner: -
--

CREATE FUNCTION public.award_achievements_batch() RETURNS TABLE(user_id integer, achievement_id integer, achievement_name character varying)
    LANGUAGE plpgsql
    AS $$
BEGIN
    -- Достижение "Первое сообщение" (1 пост)
    INSERT INTO "GadukaGang_userachievement" (user_id, achievement_id, earned_date, awarded_by_id)
    SELECT DISTINCT 
        p.author_id,
        a.id,
        CURRENT_TIMESTAMP,
        NULL
    FROM "GadukaGang_post" p
    JOIN "GadukaGang_achievement" a ON a.name = 'Первое сообщение'
    WHERE p.is_deleted = FALSE
    AND NOT EXISTS (
        SELECT 1 FROM "GadukaGang_userachievement" ua 
        WHERE ua.user_id = p.author_id AND ua.achievement_id = a.id
    )
    GROUP BY p.author_id, a.id
    HAVING COUNT(p.id) >= 1;
    
    -- Достижение "Активный участник" (50 постов)
    INSERT INTO "GadukaGang_userachievement" (user_id, achievement_id, earned_date, awarded_by_id)
    SELECT DISTINCT 
        p.author_id,
        a.id,
        CURRENT_TIMESTAMP,
        NULL
    FROM "GadukaGang_post" p
    JOIN "GadukaGang_achievement" a ON a.name = 'Активный участник'
    WHERE p.is_deleted = FALSE
    AND NOT EXISTS (
        SELECT 1 FROM "GadukaGang_userachievement" ua 
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
    FROM "GadukaGang_userachievement" ua
    JOIN "GadukaGang_achievement" a ON ua.achievement_id = a.id
    WHERE ua.earned_date >= CURRENT_TIMESTAMP - INTERVAL '1 minute';
END;
$$;


--
-- Name: award_points_for_achievement(); Type: FUNCTION; Schema: public; Owner: -
--

CREATE FUNCTION public.award_points_for_achievement() RETURNS trigger
    LANGUAGE plpgsql
    AS $$
BEGIN
    IF (TG_OP = 'INSERT') THEN
        -- Начисляем 10 очков за каждое достижение
        UPDATE "GadukaGang_userrankprogress"
        SET current_points = current_points + 10
        WHERE user_id = NEW.user_id;
        
        -- Логируем выдачу достижения
        INSERT INTO "GadukaGang_systemlog" (
            user_id,
            action_type,
            action_level,
            description,
            affected_resource_type,
            affected_resource_id,
            timestamp
        ) VALUES (
            NEW.user_id,
            'achievement_earned',
            'user',
            'Получено достижение #' || NEW.achievement_id,
            'achievement',
            NEW.achievement_id,
            CURRENT_TIMESTAMP
        );
        
        RETURN NEW;
    END IF;
    RETURN NULL;
END;
$$;


--
-- Name: batch_update_topic_ratings(); Type: FUNCTION; Schema: public; Owner: -
--

CREATE FUNCTION public.batch_update_topic_ratings() RETURNS TABLE(updated_count integer, execution_time interval)
    LANGUAGE plpgsql
    AS $$
DECLARE
    start_time TIMESTAMP;
    end_time TIMESTAMP;
    affected_rows INTEGER;
BEGIN
    start_time := clock_timestamp();
    
    -- Обновляем средний рейтинг и количество оценок для всех тем
    WITH rating_stats AS (
        SELECT 
            topic_id,
            AVG(rating)::NUMERIC(3,2) as avg_rating,
            COUNT(*)::INTEGER as rating_count
        FROM "GadukaGang_topicrating"
        GROUP BY topic_id
    )
    UPDATE "GadukaGang_topic" t
    SET 
        average_rating = COALESCE(rs.avg_rating, 0.0),
        rating_count = COALESCE(rs.rating_count, 0)
    FROM rating_stats rs
    WHERE t.id = rs.topic_id;
    
    GET DIAGNOSTICS affected_rows = ROW_COUNT;
    end_time := clock_timestamp();
    
    RETURN QUERY SELECT affected_rows, (end_time - start_time);
END;
$$;


--
-- Name: calculate_rank_progress(integer); Type: FUNCTION; Schema: public; Owner: -
--

CREATE FUNCTION public.calculate_rank_progress(p_user_id integer) RETURNS integer
    LANGUAGE plpgsql
    AS $$
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
$$;


--
-- Name: calculate_user_statistics(integer); Type: FUNCTION; Schema: public; Owner: -
--

CREATE FUNCTION public.calculate_user_statistics(p_user_id integer) RETURNS TABLE(total_posts integer, total_topics integer, total_likes integer, total_dislikes integer, achievements_count integer, rank_name character varying, rank_progress integer)
    LANGUAGE plpgsql
    AS $$
BEGIN
    RETURN QUERY
    SELECT 
        COALESCE(COUNT(DISTINCT p.id), 0)::INTEGER as total_posts,
        COALESCE(COUNT(DISTINCT t.id), 0)::INTEGER as total_topics,
        COALESCE(SUM(p.like_count), 0)::INTEGER as total_likes,
        COALESCE(SUM(p.dislike_count), 0)::INTEGER as total_dislikes,
        COALESCE(COUNT(DISTINCT ua.achievement_id), 0)::INTEGER as achievements_count,
        COALESCE(ur.name, 'Новичок')::VARCHAR(50) as rank_name,
        COALESCE(urp.progress_percentage, 0)::INTEGER as rank_progress
    FROM "GadukaGang_user" u
    LEFT JOIN "GadukaGang_userprofile" up ON u.id = up.user_id
    LEFT JOIN "GadukaGang_post" p ON u.id = p.author_id AND p.is_deleted = FALSE
    LEFT JOIN "GadukaGang_topic" t ON u.id = t.author_id
    LEFT JOIN "GadukaGang_userachievement" ua ON u.id = ua.user_id
    LEFT JOIN "GadukaGang_userrankprogress" urp ON u.id = urp.user_id
    LEFT JOIN "GadukaGang_userrank" ur ON urp.rank_id = ur.id
    WHERE u.id = p_user_id
    GROUP BY ur.name, urp.progress_percentage;
END;
$$;


--
-- Name: check_user_permission(integer, public.user_role_enum); Type: FUNCTION; Schema: public; Owner: -
--

CREATE FUNCTION public.check_user_permission(p_user_id integer, required_role public.user_role_enum) RETURNS boolean
    LANGUAGE plpgsql
    AS $$
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
$$;


--
-- Name: create_backup_log(); Type: FUNCTION; Schema: public; Owner: -
--

CREATE FUNCTION public.create_backup_log() RETURNS void
    LANGUAGE plpgsql
    AS $$
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
$$;


--
-- Name: create_new_user(character varying, character varying, character varying); Type: FUNCTION; Schema: public; Owner: -
--

CREATE FUNCTION public.create_new_user(p_username character varying, p_email character varying, p_password_hash character varying) RETURNS integer
    LANGUAGE plpgsql
    AS $$
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
$$;


--
-- Name: generate_analytics_report(timestamp without time zone, timestamp without time zone); Type: FUNCTION; Schema: public; Owner: -
--

CREATE FUNCTION public.generate_analytics_report(p_date_from timestamp without time zone DEFAULT NULL::timestamp without time zone, p_date_to timestamp without time zone DEFAULT NULL::timestamp without time zone) RETURNS TABLE(metric_name character varying, metric_value numeric, metric_change_percent numeric)
    LANGUAGE plpgsql
    AS $$
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
        SELECT COUNT(*) as cnt FROM "GadukaGang_user" 
        WHERE registration_date BETWEEN v_date_from AND v_date_to
    ),
    prev_users AS (
        SELECT COUNT(*) as cnt FROM "GadukaGang_user" 
        WHERE registration_date BETWEEN v_prev_period_from AND v_prev_period_to
    ),
    -- Новые темы
    current_topics AS (
        SELECT COUNT(*) as cnt FROM "GadukaGang_topic" 
        WHERE created_date BETWEEN v_date_from AND v_date_to
    ),
    prev_topics AS (
        SELECT COUNT(*) as cnt FROM "GadukaGang_topic" 
        WHERE created_date BETWEEN v_prev_period_from AND v_prev_period_to
    ),
    -- Новые посты
    current_posts AS (
        SELECT COUNT(*) as cnt FROM "GadukaGang_post" 
        WHERE created_date BETWEEN v_date_from AND v_date_to AND is_deleted = FALSE
    ),
    prev_posts AS (
        SELECT COUNT(*) as cnt FROM "GadukaGang_post" 
        WHERE created_date BETWEEN v_prev_period_from AND v_prev_period_to AND is_deleted = FALSE
    ),
    -- Активные пользователи
    current_active AS (
        SELECT COUNT(DISTINCT author_id) as cnt FROM "GadukaGang_post" 
        WHERE created_date BETWEEN v_date_from AND v_date_to AND is_deleted = FALSE
    ),
    prev_active AS (
        SELECT COUNT(DISTINCT author_id) as cnt FROM "GadukaGang_post" 
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
$$;


--
-- Name: process_complaint(integer, integer, public.complaint_status_enum, text); Type: FUNCTION; Schema: public; Owner: -
--

CREATE FUNCTION public.process_complaint(p_complaint_id integer, p_moderator_id integer, p_resolution public.complaint_status_enum, p_notes text) RETURNS void
    LANGUAGE plpgsql
    AS $$
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
$$;


--
-- Name: process_complaint_transaction(integer, integer, character varying, text); Type: FUNCTION; Schema: public; Owner: -
--

CREATE FUNCTION public.process_complaint_transaction(p_complaint_id integer, p_moderator_id integer, p_new_status character varying, p_action_description text) RETURNS boolean
    LANGUAGE plpgsql
    AS $$
DECLARE
    v_complaint_exists BOOLEAN;
BEGIN
    -- Проверяем существование жалобы
    SELECT EXISTS(
        SELECT 1 FROM "GadukaGang_complaint" WHERE id = p_complaint_id
    ) INTO v_complaint_exists;
    
    IF NOT v_complaint_exists THEN
        RAISE EXCEPTION 'Жалоба с ID % не найдена', p_complaint_id;
    END IF;
    
    -- Начинаем транзакцию
    BEGIN
        -- Обновляем статус жалобы
        UPDATE "GadukaGang_complaint"
        SET 
            status = p_new_status,
            assigned_moderator_id = p_moderator_id,
            resolved_date = CASE WHEN p_new_status IN ('resolved', 'dismissed') 
                                 THEN CURRENT_TIMESTAMP 
                                 ELSE resolved_date END
        WHERE id = p_complaint_id;
        
        -- Логируем действие модератора
        INSERT INTO "GadukaGang_moderatoraction" (
            moderator_id,
            action_type,
            description,
            target_type,
            target_id,
            created_date
        ) VALUES (
            p_moderator_id,
            'process_complaint',
            p_action_description,
            'complaint',
            p_complaint_id,
            CURRENT_TIMESTAMP
        );
        
        -- Логируем в системный лог
        INSERT INTO "GadukaGang_systemlog" (
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
            'moderator',
            'Жалоба #' || p_complaint_id || ' обработана: ' || p_new_status,
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
$$;


--
-- Name: search_topics_by_tags(text[]); Type: FUNCTION; Schema: public; Owner: -
--

CREATE FUNCTION public.search_topics_by_tags(tag_names text[]) RETURNS TABLE(topic_id integer)
    LANGUAGE plpgsql
    AS $$
BEGIN
    RETURN QUERY
    SELECT DISTINCT t.id
    FROM topics t
    JOIN topic_tags tt ON t.id = tt.topic_id
    JOIN tags tg ON tt.tag_id = tg.id
    WHERE tg.name = ANY(tag_names);
END;
$$;


--
-- Name: update_post_count(); Type: FUNCTION; Schema: public; Owner: -
--

CREATE FUNCTION public.update_post_count() RETURNS trigger
    LANGUAGE plpgsql
    AS $$
BEGIN
    IF (TG_OP = 'INSERT') THEN
        UPDATE "GadukaGang_userprofile"
        SET post_count = post_count + 1
        WHERE user_id = NEW.author_id;
        RETURN NEW;
    ELSIF (TG_OP = 'DELETE') THEN
        UPDATE "GadukaGang_userprofile"
        SET post_count = GREATEST(0, post_count - 1)
        WHERE user_id = OLD.author_id;
        RETURN OLD;
    ELSIF (TG_OP = 'UPDATE') THEN
        -- Если пост помечен как удалённый
        IF OLD.is_deleted = FALSE AND NEW.is_deleted = TRUE THEN
            UPDATE "GadukaGang_userprofile"
            SET post_count = GREATEST(0, post_count - 1)
            WHERE user_id = NEW.author_id;
        ELSIF OLD.is_deleted = TRUE AND NEW.is_deleted = FALSE THEN
            UPDATE "GadukaGang_userprofile"
            SET post_count = post_count + 1
            WHERE user_id = NEW.author_id;
        END IF;
        RETURN NEW;
    END IF;
    RETURN NULL;
END;
$$;


--
-- Name: update_topic_last_post(); Type: FUNCTION; Schema: public; Owner: -
--

CREATE FUNCTION public.update_topic_last_post() RETURNS trigger
    LANGUAGE plpgsql
    AS $$
BEGIN
    IF (TG_OP = 'INSERT') THEN
        UPDATE "GadukaGang_topic"
        SET last_post_date = NEW.created_date
        WHERE id = NEW.topic_id;
        RETURN NEW;
    END IF;
    RETURN NULL;
END;
$$;


--
-- Name: update_topic_last_post_date(); Type: FUNCTION; Schema: public; Owner: -
--

CREATE FUNCTION public.update_topic_last_post_date() RETURNS trigger
    LANGUAGE plpgsql
    AS $$
BEGIN
    IF (TG_OP = 'INSERT') THEN
        UPDATE topics 
        SET last_post_date = NEW.created_date 
        WHERE id = NEW.topic_id;
        RETURN NEW;
    END IF;
    RETURN NULL;
END;
$$;


--
-- Name: update_user_last_activity(); Type: FUNCTION; Schema: public; Owner: -
--

CREATE FUNCTION public.update_user_last_activity() RETURNS trigger
    LANGUAGE plpgsql
    AS $$
BEGIN
    IF (TG_OP = 'INSERT' OR TG_OP = 'UPDATE') THEN
        UPDATE "GadukaGang_userprofile"
        SET last_activity = CURRENT_TIMESTAMP
        WHERE user_id = NEW.author_id;
        RETURN NEW;
    END IF;
    RETURN NULL;
END;
$$;


--
-- Name: update_user_post_count(); Type: FUNCTION; Schema: public; Owner: -
--

CREATE FUNCTION public.update_user_post_count() RETURNS trigger
    LANGUAGE plpgsql
    AS $$
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
$$;


--
-- Name: update_user_ranks(); Type: FUNCTION; Schema: public; Owner: -
--

CREATE FUNCTION public.update_user_ranks() RETURNS TABLE(user_id integer, old_rank character varying, new_rank character varying, current_points integer)
    LANGUAGE plpgsql
    AS $$
BEGIN
    RETURN QUERY
    WITH user_points AS (
        SELECT 
            urp.user_id,
            urp.current_points,
            urp.rank_id as old_rank_id,
            (SELECT id FROM "GadukaGang_userrank" 
             WHERE required_points <= urp.current_points 
             ORDER BY required_points DESC LIMIT 1) as new_rank_id
        FROM "GadukaGang_userrankprogress" urp
    ),
    rank_updates AS (
        UPDATE "GadukaGang_userrankprogress" urp
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
    LEFT JOIN "GadukaGang_userrank" old_r ON ru.old_rank_id = old_r.id
    LEFT JOIN "GadukaGang_userrank" new_r ON ru.new_rank_id = new_r.id;
END;
$$;


--
-- Name: validate_subscription(); Type: FUNCTION; Schema: public; Owner: -
--

CREATE FUNCTION public.validate_subscription() RETURNS trigger
    LANGUAGE plpgsql
    AS $$
BEGIN
    -- Проверяем, что пользователь не подписывается сам на себя
    IF NEW.subscriber_id = NEW.subscribed_to_id THEN
        RAISE EXCEPTION 'Пользователь не может подписаться сам на себя';
    END IF;
    RETURN NEW;
END;
$$;


SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- Name: GadukaGang_achievement; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public."GadukaGang_achievement" (
    id bigint NOT NULL,
    name character varying(100) NOT NULL,
    description text NOT NULL,
    icon_url character varying(500) NOT NULL,
    criteria jsonb NOT NULL
);


--
-- Name: GadukaGang_achievement_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

ALTER TABLE public."GadukaGang_achievement" ALTER COLUMN id ADD GENERATED BY DEFAULT AS IDENTITY (
    SEQUENCE NAME public."GadukaGang_achievement_id_seq"
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1
);


--
-- Name: GadukaGang_adminlog; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public."GadukaGang_adminlog" (
    id bigint NOT NULL,
    action_type character varying(50) NOT NULL,
    description text NOT NULL,
    affected_resource_type character varying(50) NOT NULL,
    affected_resource_id integer,
    created_date timestamp with time zone NOT NULL,
    admin_id bigint
);


--
-- Name: GadukaGang_adminlog_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

ALTER TABLE public."GadukaGang_adminlog" ALTER COLUMN id ADD GENERATED BY DEFAULT AS IDENTITY (
    SEQUENCE NAME public."GadukaGang_adminlog_id_seq"
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1
);


--
-- Name: GadukaGang_certificate; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public."GadukaGang_certificate" (
    id bigint NOT NULL,
    name character varying(100) NOT NULL,
    description text NOT NULL,
    template_url character varying(500) NOT NULL,
    criteria jsonb NOT NULL
);


--
-- Name: GadukaGang_certificate_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

ALTER TABLE public."GadukaGang_certificate" ALTER COLUMN id ADD GENERATED BY DEFAULT AS IDENTITY (
    SEQUENCE NAME public."GadukaGang_certificate_id_seq"
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1
);


--
-- Name: GadukaGang_chat; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public."GadukaGang_chat" (
    id bigint NOT NULL,
    name character varying(100) NOT NULL,
    chat_type character varying(20) NOT NULL,
    created_date timestamp with time zone NOT NULL,
    is_active boolean NOT NULL,
    created_by_id bigint
);


--
-- Name: GadukaGang_chat_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

ALTER TABLE public."GadukaGang_chat" ALTER COLUMN id ADD GENERATED BY DEFAULT AS IDENTITY (
    SEQUENCE NAME public."GadukaGang_chat_id_seq"
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1
);


--
-- Name: GadukaGang_chatmessage; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public."GadukaGang_chatmessage" (
    id bigint NOT NULL,
    content text NOT NULL,
    sent_date timestamp with time zone NOT NULL,
    is_edited boolean NOT NULL,
    edited_date timestamp with time zone,
    is_deleted boolean NOT NULL,
    chat_id bigint NOT NULL,
    sender_id bigint NOT NULL
);


--
-- Name: GadukaGang_chatmessage_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

ALTER TABLE public."GadukaGang_chatmessage" ALTER COLUMN id ADD GENERATED BY DEFAULT AS IDENTITY (
    SEQUENCE NAME public."GadukaGang_chatmessage_id_seq"
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1
);


--
-- Name: GadukaGang_chatparticipant; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public."GadukaGang_chatparticipant" (
    id bigint NOT NULL,
    joined_date timestamp with time zone NOT NULL,
    left_date timestamp with time zone,
    role_in_chat character varying(20) NOT NULL,
    chat_id bigint NOT NULL,
    user_id bigint NOT NULL
);


--
-- Name: GadukaGang_chatparticipant_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

ALTER TABLE public."GadukaGang_chatparticipant" ALTER COLUMN id ADD GENERATED BY DEFAULT AS IDENTITY (
    SEQUENCE NAME public."GadukaGang_chatparticipant_id_seq"
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1
);


--
-- Name: GadukaGang_community; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public."GadukaGang_community" (
    id bigint NOT NULL,
    name character varying(100) NOT NULL,
    description text NOT NULL,
    created_date timestamp with time zone NOT NULL,
    is_active boolean NOT NULL,
    member_count integer NOT NULL,
    icon_url character varying(500) NOT NULL,
    is_private boolean NOT NULL,
    creator_id bigint,
    invite_token character varying(64)
);


--
-- Name: GadukaGang_community_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

ALTER TABLE public."GadukaGang_community" ALTER COLUMN id ADD GENERATED BY DEFAULT AS IDENTITY (
    SEQUENCE NAME public."GadukaGang_community_id_seq"
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1
);


--
-- Name: GadukaGang_communitymembership; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public."GadukaGang_communitymembership" (
    id bigint NOT NULL,
    joined_date timestamp with time zone NOT NULL,
    role character varying(20) NOT NULL,
    community_id bigint NOT NULL,
    user_id bigint NOT NULL
);


--
-- Name: GadukaGang_communitymembership_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

ALTER TABLE public."GadukaGang_communitymembership" ALTER COLUMN id ADD GENERATED BY DEFAULT AS IDENTITY (
    SEQUENCE NAME public."GadukaGang_communitymembership_id_seq"
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1
);


--
-- Name: GadukaGang_communitynotificationsubscription; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public."GadukaGang_communitynotificationsubscription" (
    id bigint NOT NULL,
    notify_on_new_post boolean NOT NULL,
    created_date timestamp with time zone NOT NULL,
    community_id bigint NOT NULL,
    user_id bigint NOT NULL
);


--
-- Name: GadukaGang_communitynotificationsubscription_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

ALTER TABLE public."GadukaGang_communitynotificationsubscription" ALTER COLUMN id ADD GENERATED BY DEFAULT AS IDENTITY (
    SEQUENCE NAME public."GadukaGang_communitynotificationsubscription_id_seq"
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1
);


--
-- Name: GadukaGang_communitytopic; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public."GadukaGang_communitytopic" (
    id bigint NOT NULL,
    created_date timestamp with time zone NOT NULL,
    community_id bigint NOT NULL,
    topic_id bigint NOT NULL
);


--
-- Name: GadukaGang_communitytopic_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

ALTER TABLE public."GadukaGang_communitytopic" ALTER COLUMN id ADD GENERATED BY DEFAULT AS IDENTITY (
    SEQUENCE NAME public."GadukaGang_communitytopic_id_seq"
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1
);


--
-- Name: GadukaGang_complaint; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public."GadukaGang_complaint" (
    id bigint NOT NULL,
    target_type character varying(20) NOT NULL,
    target_id integer NOT NULL,
    reason character varying(100) NOT NULL,
    description text NOT NULL,
    status character varying(20) NOT NULL,
    created_date timestamp with time zone NOT NULL,
    resolved_date timestamp with time zone,
    assigned_moderator_id bigint,
    reporter_id bigint NOT NULL
);


--
-- Name: GadukaGang_complaint_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

ALTER TABLE public."GadukaGang_complaint" ALTER COLUMN id ADD GENERATED BY DEFAULT AS IDENTITY (
    SEQUENCE NAME public."GadukaGang_complaint_id_seq"
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1
);


--
-- Name: GadukaGang_course; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public."GadukaGang_course" (
    id bigint NOT NULL,
    title character varying(200) NOT NULL,
    description text NOT NULL,
    icon_url character varying(500) NOT NULL,
    created_date timestamp with time zone NOT NULL,
    "order" integer NOT NULL,
    is_active boolean NOT NULL
);


--
-- Name: GadukaGang_course_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

ALTER TABLE public."GadukaGang_course" ALTER COLUMN id ADD GENERATED BY DEFAULT AS IDENTITY (
    SEQUENCE NAME public."GadukaGang_course_id_seq"
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1
);


--
-- Name: GadukaGang_courseprogress; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public."GadukaGang_courseprogress" (
    id bigint NOT NULL,
    started_date timestamp with time zone NOT NULL,
    completed_date timestamp with time zone,
    is_completed boolean NOT NULL,
    course_id bigint NOT NULL,
    user_id bigint NOT NULL
);


--
-- Name: GadukaGang_courseprogress_completed_lessons; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public."GadukaGang_courseprogress_completed_lessons" (
    id bigint NOT NULL,
    courseprogress_id bigint NOT NULL,
    lesson_id bigint NOT NULL
);


--
-- Name: GadukaGang_courseprogress_completed_lessons_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

ALTER TABLE public."GadukaGang_courseprogress_completed_lessons" ALTER COLUMN id ADD GENERATED BY DEFAULT AS IDENTITY (
    SEQUENCE NAME public."GadukaGang_courseprogress_completed_lessons_id_seq"
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1
);


--
-- Name: GadukaGang_courseprogress_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

ALTER TABLE public."GadukaGang_courseprogress" ALTER COLUMN id ADD GENERATED BY DEFAULT AS IDENTITY (
    SEQUENCE NAME public."GadukaGang_courseprogress_id_seq"
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1
);


--
-- Name: GadukaGang_forumsetting; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public."GadukaGang_forumsetting" (
    id bigint NOT NULL,
    setting_name character varying(100) NOT NULL,
    setting_value jsonb NOT NULL,
    category character varying(50) NOT NULL,
    last_modified timestamp with time zone NOT NULL,
    modified_by_id bigint
);


--
-- Name: GadukaGang_forumsetting_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

ALTER TABLE public."GadukaGang_forumsetting" ALTER COLUMN id ADD GENERATED BY DEFAULT AS IDENTITY (
    SEQUENCE NAME public."GadukaGang_forumsetting_id_seq"
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1
);


--
-- Name: GadukaGang_githubauth; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public."GadukaGang_githubauth" (
    id bigint NOT NULL,
    github_id character varying(100) NOT NULL,
    github_username character varying(150) NOT NULL,
    access_token character varying(500) NOT NULL,
    refresh_token character varying(500) NOT NULL,
    created_date timestamp with time zone NOT NULL,
    last_sync timestamp with time zone NOT NULL,
    user_id bigint NOT NULL
);


--
-- Name: GadukaGang_githubauth_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

ALTER TABLE public."GadukaGang_githubauth" ALTER COLUMN id ADD GENERATED BY DEFAULT AS IDENTITY (
    SEQUENCE NAME public."GadukaGang_githubauth_id_seq"
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1
);


--
-- Name: GadukaGang_lesson; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public."GadukaGang_lesson" (
    id bigint NOT NULL,
    title character varying(200) NOT NULL,
    content text NOT NULL,
    lesson_type character varying(20) NOT NULL,
    "order" integer NOT NULL,
    created_date timestamp with time zone NOT NULL,
    practice_code_template text NOT NULL,
    practice_solution text NOT NULL,
    course_id bigint NOT NULL,
    test_input text NOT NULL,
    test_output text NOT NULL,
    test_cases jsonb NOT NULL
);


--
-- Name: GadukaGang_lesson_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

ALTER TABLE public."GadukaGang_lesson" ALTER COLUMN id ADD GENERATED BY DEFAULT AS IDENTITY (
    SEQUENCE NAME public."GadukaGang_lesson_id_seq"
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1
);


--
-- Name: GadukaGang_moderatoraction; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public."GadukaGang_moderatoraction" (
    id bigint NOT NULL,
    action_type character varying(50) NOT NULL,
    description text NOT NULL,
    target_type character varying(50) NOT NULL,
    target_id integer NOT NULL,
    created_date timestamp with time zone NOT NULL,
    moderator_id bigint
);


--
-- Name: GadukaGang_moderatoraction_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

ALTER TABLE public."GadukaGang_moderatoraction" ALTER COLUMN id ADD GENERATED BY DEFAULT AS IDENTITY (
    SEQUENCE NAME public."GadukaGang_moderatoraction_id_seq"
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1
);


--
-- Name: GadukaGang_notification; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public."GadukaGang_notification" (
    id bigint NOT NULL,
    notification_type character varying(50) NOT NULL,
    title character varying(200) NOT NULL,
    message text NOT NULL,
    is_read boolean NOT NULL,
    created_date timestamp with time zone NOT NULL,
    related_resource_type character varying(50) NOT NULL,
    related_resource_id integer,
    user_id bigint NOT NULL
);


--
-- Name: GadukaGang_notification_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

ALTER TABLE public."GadukaGang_notification" ALTER COLUMN id ADD GENERATED BY DEFAULT AS IDENTITY (
    SEQUENCE NAME public."GadukaGang_notification_id_seq"
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1
);


--
-- Name: GadukaGang_post; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public."GadukaGang_post" (
    id bigint NOT NULL,
    content text NOT NULL,
    created_date timestamp with time zone NOT NULL,
    last_edited_date timestamp with time zone,
    edit_count integer NOT NULL,
    is_deleted boolean NOT NULL,
    topic_id bigint NOT NULL,
    author_id bigint NOT NULL,
    dislike_count integer NOT NULL,
    like_count integer NOT NULL
);


--
-- Name: GadukaGang_post_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

ALTER TABLE public."GadukaGang_post" ALTER COLUMN id ADD GENERATED BY DEFAULT AS IDENTITY (
    SEQUENCE NAME public."GadukaGang_post_id_seq"
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1
);


--
-- Name: GadukaGang_postlike; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public."GadukaGang_postlike" (
    id bigint NOT NULL,
    like_type character varying(10) NOT NULL,
    created_date timestamp with time zone NOT NULL,
    post_id bigint NOT NULL,
    user_id bigint NOT NULL
);


--
-- Name: GadukaGang_postlike_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

ALTER TABLE public."GadukaGang_postlike" ALTER COLUMN id ADD GENERATED BY DEFAULT AS IDENTITY (
    SEQUENCE NAME public."GadukaGang_postlike_id_seq"
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1
);


--
-- Name: GadukaGang_searchindex; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public."GadukaGang_searchindex" (
    id bigint NOT NULL,
    content_type character varying(50) NOT NULL,
    object_id integer NOT NULL,
    search_vector text NOT NULL,
    tags text NOT NULL,
    author_username character varying(150) NOT NULL,
    created_date timestamp with time zone NOT NULL,
    last_updated timestamp with time zone NOT NULL
);


--
-- Name: GadukaGang_searchindex_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

ALTER TABLE public."GadukaGang_searchindex" ALTER COLUMN id ADD GENERATED BY DEFAULT AS IDENTITY (
    SEQUENCE NAME public."GadukaGang_searchindex_id_seq"
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1
);


--
-- Name: GadukaGang_section; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public."GadukaGang_section" (
    id bigint NOT NULL,
    name character varying(100) NOT NULL,
    description text NOT NULL,
    created_date timestamp with time zone NOT NULL,
    created_by_id bigint
);


--
-- Name: GadukaGang_section_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

ALTER TABLE public."GadukaGang_section" ALTER COLUMN id ADD GENERATED BY DEFAULT AS IDENTITY (
    SEQUENCE NAME public."GadukaGang_section_id_seq"
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1
);


--
-- Name: GadukaGang_systemlog; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public."GadukaGang_systemlog" (
    id bigint NOT NULL,
    action_type character varying(50) NOT NULL,
    action_level character varying(20) NOT NULL,
    description text NOT NULL,
    affected_resource_type character varying(50) NOT NULL,
    affected_resource_id integer,
    "timestamp" timestamp with time zone NOT NULL,
    user_id bigint
);


--
-- Name: GadukaGang_systemlog_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

ALTER TABLE public."GadukaGang_systemlog" ALTER COLUMN id ADD GENERATED BY DEFAULT AS IDENTITY (
    SEQUENCE NAME public."GadukaGang_systemlog_id_seq"
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1
);


--
-- Name: GadukaGang_tag; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public."GadukaGang_tag" (
    id bigint NOT NULL,
    name character varying(50) NOT NULL,
    color character varying(7) NOT NULL
);


--
-- Name: GadukaGang_tag_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

ALTER TABLE public."GadukaGang_tag" ALTER COLUMN id ADD GENERATED BY DEFAULT AS IDENTITY (
    SEQUENCE NAME public."GadukaGang_tag_id_seq"
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1
);


--
-- Name: GadukaGang_topic; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public."GadukaGang_topic" (
    id bigint NOT NULL,
    title character varying(255) NOT NULL,
    created_date timestamp with time zone NOT NULL,
    last_post_date timestamp with time zone NOT NULL,
    is_pinned boolean NOT NULL,
    view_count integer NOT NULL,
    section_id bigint NOT NULL,
    author_id bigint NOT NULL,
    average_rating double precision NOT NULL,
    rating_count integer NOT NULL
);


--
-- Name: GadukaGang_topic_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

ALTER TABLE public."GadukaGang_topic" ALTER COLUMN id ADD GENERATED BY DEFAULT AS IDENTITY (
    SEQUENCE NAME public."GadukaGang_topic_id_seq"
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1
);


--
-- Name: GadukaGang_topicrating; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public."GadukaGang_topicrating" (
    id bigint NOT NULL,
    rating integer NOT NULL,
    created_date timestamp with time zone NOT NULL,
    topic_id bigint NOT NULL,
    user_id bigint NOT NULL
);


--
-- Name: GadukaGang_topicrating_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

ALTER TABLE public."GadukaGang_topicrating" ALTER COLUMN id ADD GENERATED BY DEFAULT AS IDENTITY (
    SEQUENCE NAME public."GadukaGang_topicrating_id_seq"
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1
);


--
-- Name: GadukaGang_topicsubscription; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public."GadukaGang_topicsubscription" (
    id bigint NOT NULL,
    created_date timestamp with time zone NOT NULL,
    notify_on_new_post boolean NOT NULL,
    topic_id bigint NOT NULL,
    user_id bigint NOT NULL
);


--
-- Name: GadukaGang_topicsubscription_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

ALTER TABLE public."GadukaGang_topicsubscription" ALTER COLUMN id ADD GENERATED BY DEFAULT AS IDENTITY (
    SEQUENCE NAME public."GadukaGang_topicsubscription_id_seq"
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1
);


--
-- Name: GadukaGang_topictag; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public."GadukaGang_topictag" (
    id bigint NOT NULL,
    tag_id bigint NOT NULL,
    topic_id bigint NOT NULL
);


--
-- Name: GadukaGang_topictag_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

ALTER TABLE public."GadukaGang_topictag" ALTER COLUMN id ADD GENERATED BY DEFAULT AS IDENTITY (
    SEQUENCE NAME public."GadukaGang_topictag_id_seq"
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1
);


--
-- Name: GadukaGang_topicview; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public."GadukaGang_topicview" (
    id bigint NOT NULL,
    view_date timestamp with time zone NOT NULL,
    topic_id bigint NOT NULL,
    user_id bigint NOT NULL
);


--
-- Name: GadukaGang_topicview_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

ALTER TABLE public."GadukaGang_topicview" ALTER COLUMN id ADD GENERATED BY DEFAULT AS IDENTITY (
    SEQUENCE NAME public."GadukaGang_topicview_id_seq"
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1
);


--
-- Name: GadukaGang_user; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public."GadukaGang_user" (
    id bigint NOT NULL,
    password character varying(128) NOT NULL,
    is_superuser boolean NOT NULL,
    username character varying(150) NOT NULL,
    first_name character varying(150) NOT NULL,
    last_name character varying(150) NOT NULL,
    email character varying(254) NOT NULL,
    is_staff boolean NOT NULL,
    date_joined timestamp with time zone NOT NULL,
    role character varying(20) NOT NULL,
    registration_date timestamp with time zone NOT NULL,
    last_login timestamp with time zone,
    is_active boolean NOT NULL
);


--
-- Name: GadukaGang_user_groups; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public."GadukaGang_user_groups" (
    id bigint NOT NULL,
    user_id bigint NOT NULL,
    group_id integer NOT NULL
);


--
-- Name: GadukaGang_user_groups_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

ALTER TABLE public."GadukaGang_user_groups" ALTER COLUMN id ADD GENERATED BY DEFAULT AS IDENTITY (
    SEQUENCE NAME public."GadukaGang_user_groups_id_seq"
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1
);


--
-- Name: GadukaGang_user_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

ALTER TABLE public."GadukaGang_user" ALTER COLUMN id ADD GENERATED BY DEFAULT AS IDENTITY (
    SEQUENCE NAME public."GadukaGang_user_id_seq"
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1
);


--
-- Name: GadukaGang_user_user_permissions; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public."GadukaGang_user_user_permissions" (
    id bigint NOT NULL,
    user_id bigint NOT NULL,
    permission_id integer NOT NULL
);


--
-- Name: GadukaGang_user_user_permissions_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

ALTER TABLE public."GadukaGang_user_user_permissions" ALTER COLUMN id ADD GENERATED BY DEFAULT AS IDENTITY (
    SEQUENCE NAME public."GadukaGang_user_user_permissions_id_seq"
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1
);


--
-- Name: GadukaGang_userachievement; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public."GadukaGang_userachievement" (
    id bigint NOT NULL,
    earned_date timestamp with time zone NOT NULL,
    achievement_id bigint NOT NULL,
    awarded_by_id bigint,
    user_id bigint NOT NULL
);


--
-- Name: GadukaGang_userachievement_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

ALTER TABLE public."GadukaGang_userachievement" ALTER COLUMN id ADD GENERATED BY DEFAULT AS IDENTITY (
    SEQUENCE NAME public."GadukaGang_userachievement_id_seq"
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1
);


--
-- Name: GadukaGang_usercertificate; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public."GadukaGang_usercertificate" (
    id bigint NOT NULL,
    awarded_date timestamp with time zone NOT NULL,
    expiration_date timestamp with time zone,
    certificate_id bigint NOT NULL,
    awarded_by_id bigint,
    user_id bigint NOT NULL
);


--
-- Name: GadukaGang_usercertificate_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

ALTER TABLE public."GadukaGang_usercertificate" ALTER COLUMN id ADD GENERATED BY DEFAULT AS IDENTITY (
    SEQUENCE NAME public."GadukaGang_usercertificate_id_seq"
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1
);


--
-- Name: GadukaGang_userprofile; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public."GadukaGang_userprofile" (
    user_id bigint NOT NULL,
    avatar_url character varying(500) NOT NULL,
    bio text NOT NULL,
    signature text NOT NULL,
    post_count integer NOT NULL,
    join_date timestamp with time zone NOT NULL,
    last_activity timestamp with time zone NOT NULL
);


--
-- Name: GadukaGang_userrank; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public."GadukaGang_userrank" (
    id bigint NOT NULL,
    name character varying(50) NOT NULL,
    required_points integer NOT NULL,
    icon_url character varying(500) NOT NULL
);


--
-- Name: GadukaGang_userrank_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

ALTER TABLE public."GadukaGang_userrank" ALTER COLUMN id ADD GENERATED BY DEFAULT AS IDENTITY (
    SEQUENCE NAME public."GadukaGang_userrank_id_seq"
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1
);


--
-- Name: GadukaGang_userrankprogress; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public."GadukaGang_userrankprogress" (
    user_id bigint NOT NULL,
    current_points integer NOT NULL,
    progress_percentage integer NOT NULL,
    rank_id bigint
);


--
-- Name: GadukaGang_usersubscription; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public."GadukaGang_usersubscription" (
    id bigint NOT NULL,
    created_date timestamp with time zone NOT NULL,
    subscribed_to_id bigint NOT NULL,
    subscriber_id bigint NOT NULL
);


--
-- Name: GadukaGang_usersubscription_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

ALTER TABLE public."GadukaGang_usersubscription" ALTER COLUMN id ADD GENERATED BY DEFAULT AS IDENTITY (
    SEQUENCE NAME public."GadukaGang_usersubscription_id_seq"
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1
);


--
-- Name: account_emailaddress; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.account_emailaddress (
    id integer NOT NULL,
    email character varying(254) NOT NULL,
    verified boolean NOT NULL,
    "primary" boolean NOT NULL,
    user_id bigint NOT NULL
);


--
-- Name: account_emailaddress_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

ALTER TABLE public.account_emailaddress ALTER COLUMN id ADD GENERATED BY DEFAULT AS IDENTITY (
    SEQUENCE NAME public.account_emailaddress_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1
);


--
-- Name: account_emailconfirmation; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.account_emailconfirmation (
    id integer NOT NULL,
    created timestamp with time zone NOT NULL,
    sent timestamp with time zone,
    key character varying(64) NOT NULL,
    email_address_id integer NOT NULL
);


--
-- Name: account_emailconfirmation_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

ALTER TABLE public.account_emailconfirmation ALTER COLUMN id ADD GENERATED BY DEFAULT AS IDENTITY (
    SEQUENCE NAME public.account_emailconfirmation_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1
);


--
-- Name: achievements; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.achievements (
    id integer NOT NULL,
    name character varying(100) NOT NULL,
    description text,
    icon_url character varying(500),
    criteria jsonb
);


--
-- Name: achievements_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.achievements_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: achievements_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.achievements_id_seq OWNED BY public.achievements.id;


--
-- Name: user_profiles; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.user_profiles (
    user_id integer NOT NULL,
    avatar_url character varying(500),
    bio text,
    signature text,
    post_count integer DEFAULT 0,
    join_date timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    last_activity timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);


--
-- Name: users; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.users (
    id integer NOT NULL,
    username character varying(50) NOT NULL,
    email character varying(255) NOT NULL,
    password_hash character varying(255) NOT NULL,
    registration_date timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    last_login timestamp without time zone,
    is_active boolean DEFAULT true,
    role public.user_role_enum DEFAULT 'user'::public.user_role_enum
);


--
-- Name: active_users; Type: VIEW; Schema: public; Owner: -
--

CREATE VIEW public.active_users AS
 SELECT u.id,
    u.username,
    up.last_activity,
    up.post_count
   FROM (public.users u
     JOIN public.user_profiles up ON ((u.id = up.user_id)))
  WHERE (up.last_activity >= (CURRENT_TIMESTAMP - '24:00:00'::interval))
  ORDER BY up.last_activity DESC;


--
-- Name: auth_group; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.auth_group (
    id integer NOT NULL,
    name character varying(150) NOT NULL
);


--
-- Name: auth_group_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

ALTER TABLE public.auth_group ALTER COLUMN id ADD GENERATED BY DEFAULT AS IDENTITY (
    SEQUENCE NAME public.auth_group_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1
);


--
-- Name: auth_group_permissions; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.auth_group_permissions (
    id bigint NOT NULL,
    group_id integer NOT NULL,
    permission_id integer NOT NULL
);


--
-- Name: auth_group_permissions_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

ALTER TABLE public.auth_group_permissions ALTER COLUMN id ADD GENERATED BY DEFAULT AS IDENTITY (
    SEQUENCE NAME public.auth_group_permissions_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1
);


--
-- Name: auth_permission; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.auth_permission (
    id integer NOT NULL,
    name character varying(255) NOT NULL,
    content_type_id integer NOT NULL,
    codename character varying(100) NOT NULL
);


--
-- Name: auth_permission_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

ALTER TABLE public.auth_permission ALTER COLUMN id ADD GENERATED BY DEFAULT AS IDENTITY (
    SEQUENCE NAME public.auth_permission_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1
);


--
-- Name: authtoken_token; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.authtoken_token (
    key character varying(40) NOT NULL,
    created timestamp with time zone NOT NULL,
    user_id bigint NOT NULL
);


--
-- Name: certificates; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.certificates (
    id integer NOT NULL,
    name character varying(100) NOT NULL,
    description text,
    template_url character varying(500),
    criteria jsonb
);


--
-- Name: certificates_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.certificates_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: certificates_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.certificates_id_seq OWNED BY public.certificates.id;


--
-- Name: chat_messages; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.chat_messages (
    id integer NOT NULL,
    chat_id integer NOT NULL,
    sender_id integer NOT NULL,
    content text NOT NULL,
    sent_date timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    is_edited boolean DEFAULT false,
    edited_date timestamp without time zone,
    is_deleted boolean DEFAULT false
);


--
-- Name: chat_messages_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.chat_messages_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: chat_messages_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.chat_messages_id_seq OWNED BY public.chat_messages.id;


--
-- Name: chat_participants; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.chat_participants (
    chat_id integer NOT NULL,
    user_id integer NOT NULL,
    joined_date timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    left_date timestamp without time zone,
    role_in_chat character varying(20) DEFAULT 'member'::character varying
);


--
-- Name: chats; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.chats (
    id integer NOT NULL,
    name character varying(100),
    chat_type public.chat_type_enum NOT NULL,
    created_by integer,
    created_date timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    is_active boolean DEFAULT true
);


--
-- Name: chats_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.chats_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: chats_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.chats_id_seq OWNED BY public.chats.id;


--
-- Name: complaints; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.complaints (
    id integer NOT NULL,
    reporter_id integer NOT NULL,
    target_type public.resource_type_enum NOT NULL,
    target_id integer NOT NULL,
    reason character varying(100),
    description text,
    status public.complaint_status_enum DEFAULT 'open'::public.complaint_status_enum,
    assigned_moderator integer,
    created_date timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    resolved_date timestamp without time zone
);


--
-- Name: complaints_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.complaints_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: complaints_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.complaints_id_seq OWNED BY public.complaints.id;


--
-- Name: django_admin_log; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.django_admin_log (
    id integer NOT NULL,
    action_time timestamp with time zone NOT NULL,
    object_id text,
    object_repr character varying(200) NOT NULL,
    action_flag smallint NOT NULL,
    change_message text NOT NULL,
    content_type_id integer,
    user_id bigint NOT NULL,
    CONSTRAINT django_admin_log_action_flag_check CHECK ((action_flag >= 0))
);


--
-- Name: django_admin_log_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

ALTER TABLE public.django_admin_log ALTER COLUMN id ADD GENERATED BY DEFAULT AS IDENTITY (
    SEQUENCE NAME public.django_admin_log_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1
);


--
-- Name: django_content_type; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.django_content_type (
    id integer NOT NULL,
    app_label character varying(100) NOT NULL,
    model character varying(100) NOT NULL
);


--
-- Name: django_content_type_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

ALTER TABLE public.django_content_type ALTER COLUMN id ADD GENERATED BY DEFAULT AS IDENTITY (
    SEQUENCE NAME public.django_content_type_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1
);


--
-- Name: django_migrations; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.django_migrations (
    id bigint NOT NULL,
    app character varying(255) NOT NULL,
    name character varying(255) NOT NULL,
    applied timestamp with time zone NOT NULL
);


--
-- Name: django_migrations_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

ALTER TABLE public.django_migrations ALTER COLUMN id ADD GENERATED BY DEFAULT AS IDENTITY (
    SEQUENCE NAME public.django_migrations_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1
);


--
-- Name: django_session; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.django_session (
    session_key character varying(40) NOT NULL,
    session_data text NOT NULL,
    expire_date timestamp with time zone NOT NULL
);


--
-- Name: django_site; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.django_site (
    id integer NOT NULL,
    domain character varying(100) NOT NULL,
    name character varying(50) NOT NULL
);


--
-- Name: django_site_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

ALTER TABLE public.django_site ALTER COLUMN id ADD GENERATED BY DEFAULT AS IDENTITY (
    SEQUENCE NAME public.django_site_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1
);


--
-- Name: forum_settings; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.forum_settings (
    id integer NOT NULL,
    setting_name character varying(100) NOT NULL,
    setting_value jsonb,
    category character varying(50),
    last_modified timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    modified_by integer
);


--
-- Name: forum_settings_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.forum_settings_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: forum_settings_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.forum_settings_id_seq OWNED BY public.forum_settings.id;


--
-- Name: posts; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.posts (
    id integer NOT NULL,
    topic_id integer NOT NULL,
    author_id integer NOT NULL,
    content text NOT NULL,
    created_date timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    last_edited_date timestamp without time zone,
    edit_count integer DEFAULT 0,
    is_deleted boolean DEFAULT false
);


--
-- Name: posts_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.posts_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: posts_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.posts_id_seq OWNED BY public.posts.id;


--
-- Name: sections; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.sections (
    id integer NOT NULL,
    name character varying(100) NOT NULL,
    description text,
    created_by integer,
    created_date timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);


--
-- Name: sections_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.sections_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: sections_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.sections_id_seq OWNED BY public.sections.id;


--
-- Name: socialaccount_socialaccount; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.socialaccount_socialaccount (
    id integer NOT NULL,
    provider character varying(200) NOT NULL,
    uid character varying(191) NOT NULL,
    last_login timestamp with time zone NOT NULL,
    date_joined timestamp with time zone NOT NULL,
    extra_data text NOT NULL,
    user_id bigint NOT NULL
);


--
-- Name: socialaccount_socialaccount_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

ALTER TABLE public.socialaccount_socialaccount ALTER COLUMN id ADD GENERATED BY DEFAULT AS IDENTITY (
    SEQUENCE NAME public.socialaccount_socialaccount_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1
);


--
-- Name: socialaccount_socialapp; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.socialaccount_socialapp (
    id integer NOT NULL,
    provider character varying(30) NOT NULL,
    name character varying(40) NOT NULL,
    client_id character varying(191) NOT NULL,
    secret character varying(191) NOT NULL,
    key character varying(191) NOT NULL,
    provider_id character varying(200) NOT NULL,
    settings jsonb NOT NULL
);


--
-- Name: socialaccount_socialapp_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

ALTER TABLE public.socialaccount_socialapp ALTER COLUMN id ADD GENERATED BY DEFAULT AS IDENTITY (
    SEQUENCE NAME public.socialaccount_socialapp_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1
);


--
-- Name: socialaccount_socialapp_sites; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.socialaccount_socialapp_sites (
    id bigint NOT NULL,
    socialapp_id integer NOT NULL,
    site_id integer NOT NULL
);


--
-- Name: socialaccount_socialapp_sites_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

ALTER TABLE public.socialaccount_socialapp_sites ALTER COLUMN id ADD GENERATED BY DEFAULT AS IDENTITY (
    SEQUENCE NAME public.socialaccount_socialapp_sites_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1
);


--
-- Name: socialaccount_socialtoken; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.socialaccount_socialtoken (
    id integer NOT NULL,
    token text NOT NULL,
    token_secret text NOT NULL,
    expires_at timestamp with time zone,
    account_id integer NOT NULL,
    app_id integer
);


--
-- Name: socialaccount_socialtoken_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

ALTER TABLE public.socialaccount_socialtoken ALTER COLUMN id ADD GENERATED BY DEFAULT AS IDENTITY (
    SEQUENCE NAME public.socialaccount_socialtoken_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1
);


--
-- Name: system_logs; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.system_logs (
    id integer NOT NULL,
    user_id integer,
    action_type character varying(50) NOT NULL,
    action_level public.user_role_enum NOT NULL,
    description text,
    affected_resource_type character varying(50),
    affected_resource_id integer,
    "timestamp" timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);


--
-- Name: system_logs_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.system_logs_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: system_logs_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.system_logs_id_seq OWNED BY public.system_logs.id;


--
-- Name: tags; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.tags (
    id integer NOT NULL,
    name character varying(50) NOT NULL,
    color character varying(7) DEFAULT '#000000'::character varying
);


--
-- Name: tags_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.tags_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: tags_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.tags_id_seq OWNED BY public.tags.id;


--
-- Name: topics; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.topics (
    id integer NOT NULL,
    section_id integer NOT NULL,
    title character varying(255) NOT NULL,
    author_id integer NOT NULL,
    created_date timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    last_post_date timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    is_pinned boolean DEFAULT false,
    view_count integer DEFAULT 0
);


--
-- Name: topic_statistics; Type: VIEW; Schema: public; Owner: -
--

CREATE VIEW public.topic_statistics AS
 SELECT t.id,
    t.title,
    t.created_date,
    t.last_post_date,
    t.view_count,
    count(p.id) AS post_count,
    s.name AS section_name
   FROM ((public.topics t
     JOIN public.sections s ON ((t.section_id = s.id)))
     LEFT JOIN public.posts p ON ((t.id = p.topic_id)))
  GROUP BY t.id, t.title, t.created_date, t.last_post_date, t.view_count, s.name;


--
-- Name: topic_tags; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.topic_tags (
    topic_id integer NOT NULL,
    tag_id integer NOT NULL
);


--
-- Name: topics_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.topics_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: topics_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.topics_id_seq OWNED BY public.topics.id;


--
-- Name: user_achievements; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.user_achievements (
    user_id integer NOT NULL,
    achievement_id integer NOT NULL,
    earned_date timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    awarded_by integer
);


--
-- Name: user_certificates; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.user_certificates (
    id integer NOT NULL,
    user_id integer NOT NULL,
    certificate_id integer NOT NULL,
    awarded_date timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    awarded_by integer,
    expiration_date timestamp without time zone
);


--
-- Name: user_certificates_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.user_certificates_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: user_certificates_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.user_certificates_id_seq OWNED BY public.user_certificates.id;


--
-- Name: user_rank_progress; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.user_rank_progress (
    user_id integer NOT NULL,
    rank_id integer,
    current_points integer DEFAULT 0,
    progress_percentage integer DEFAULT 0
);


--
-- Name: user_ranks; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.user_ranks (
    id integer NOT NULL,
    name character varying(50) NOT NULL,
    required_points integer NOT NULL,
    icon_url character varying(500)
);


--
-- Name: user_ranks_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.user_ranks_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: user_ranks_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.user_ranks_id_seq OWNED BY public.user_ranks.id;


--
-- Name: user_statistics; Type: VIEW; Schema: public; Owner: -
--

CREATE VIEW public.user_statistics AS
 SELECT u.id,
    u.username,
    u.registration_date,
    up.post_count,
    up.last_activity,
    urp.current_points,
    ur.name AS current_rank
   FROM (((public.users u
     JOIN public.user_profiles up ON ((u.id = up.user_id)))
     JOIN public.user_rank_progress urp ON ((u.id = urp.user_id)))
     LEFT JOIN public.user_ranks ur ON ((urp.rank_id = ur.id)));


--
-- Name: users_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.users_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: users_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.users_id_seq OWNED BY public.users.id;


--
-- Name: v_active_users_24h; Type: VIEW; Schema: public; Owner: -
--

CREATE VIEW public.v_active_users_24h AS
 SELECT u.id,
    u.username,
    u.role,
    up.last_activity,
    up.post_count,
    count(DISTINCT p.id) AS posts_last_24h,
    count(DISTINCT t.id) AS topics_last_24h
   FROM (((public."GadukaGang_user" u
     JOIN public."GadukaGang_userprofile" up ON ((u.id = up.user_id)))
     LEFT JOIN public."GadukaGang_post" p ON (((u.id = p.author_id) AND (p.created_date >= (CURRENT_TIMESTAMP - '24:00:00'::interval)) AND (p.is_deleted = false))))
     LEFT JOIN public."GadukaGang_topic" t ON (((u.id = t.author_id) AND (t.created_date >= (CURRENT_TIMESTAMP - '24:00:00'::interval)))))
  WHERE (up.last_activity >= (CURRENT_TIMESTAMP - '24:00:00'::interval))
  GROUP BY u.id, u.username, u.role, up.last_activity, up.post_count
  ORDER BY up.last_activity DESC;


--
-- Name: v_daily_activity; Type: VIEW; Schema: public; Owner: -
--

CREATE VIEW public.v_daily_activity AS
 SELECT date(created_date) AS activity_date,
    count(DISTINCT
        CASE
            WHEN (table_name = 'user'::text) THEN id
            ELSE NULL::bigint
        END) AS new_users,
    count(DISTINCT
        CASE
            WHEN (table_name = 'topic'::text) THEN id
            ELSE NULL::bigint
        END) AS new_topics,
    count(DISTINCT
        CASE
            WHEN (table_name = 'post'::text) THEN id
            ELSE NULL::bigint
        END) AS new_posts,
    count(DISTINCT
        CASE
            WHEN (table_name = 'post'::text) THEN author_id
            ELSE NULL::bigint
        END) AS active_users
   FROM ( SELECT "GadukaGang_topic".id,
            "GadukaGang_topic".author_id,
            "GadukaGang_topic".created_date,
            'topic'::text AS table_name
           FROM public."GadukaGang_topic"
        UNION ALL
         SELECT "GadukaGang_post".id,
            "GadukaGang_post".author_id,
            "GadukaGang_post".created_date,
            'post'::text AS table_name
           FROM public."GadukaGang_post"
          WHERE ("GadukaGang_post".is_deleted = false)
        UNION ALL
         SELECT "GadukaGang_user".id,
            "GadukaGang_user".id AS author_id,
            "GadukaGang_user".registration_date AS created_date,
            'user'::text AS table_name
           FROM public."GadukaGang_user") combined
  WHERE (created_date >= (CURRENT_TIMESTAMP - '30 days'::interval))
  GROUP BY (date(created_date))
  ORDER BY (date(created_date)) DESC;


--
-- Name: v_moderation_statistics; Type: VIEW; Schema: public; Owner: -
--

CREATE VIEW public.v_moderation_statistics AS
 SELECT u.id AS moderator_id,
    u.username AS moderator_username,
    u.role,
    count(DISTINCT ma.id) AS total_actions,
    count(DISTINCT
        CASE
            WHEN ((ma.action_type)::text = 'delete_post'::text) THEN ma.id
            ELSE NULL::bigint
        END) AS posts_deleted,
    count(DISTINCT
        CASE
            WHEN ((ma.action_type)::text = 'delete_topic'::text) THEN ma.id
            ELSE NULL::bigint
        END) AS topics_deleted,
    count(DISTINCT
        CASE
            WHEN ((ma.action_type)::text = 'block_user'::text) THEN ma.id
            ELSE NULL::bigint
        END) AS users_blocked,
    count(DISTINCT
        CASE
            WHEN ((ma.action_type)::text = 'process_complaint'::text) THEN ma.id
            ELSE NULL::bigint
        END) AS complaints_processed,
    min(ma.created_date) AS first_action_date,
    max(ma.created_date) AS last_action_date,
    count(DISTINCT date(ma.created_date)) AS active_days
   FROM (public."GadukaGang_user" u
     LEFT JOIN public."GadukaGang_moderatoraction" ma ON ((u.id = ma.moderator_id)))
  WHERE ((u.role)::text = ANY ((ARRAY['moderator'::character varying, 'admin_level_1'::character varying, 'admin_level_2'::character varying, 'admin_level_3'::character varying, 'super_admin'::character varying])::text[]))
  GROUP BY u.id, u.username, u.role
  ORDER BY (count(DISTINCT ma.id)) DESC;


--
-- Name: v_pending_complaints; Type: VIEW; Schema: public; Owner: -
--

CREATE VIEW public.v_pending_complaints AS
 SELECT c.id,
    c.target_type,
    c.target_id,
    c.reason,
    c.description,
    c.status,
    c.created_date,
    reporter.username AS reporter_username,
    reporter.id AS reporter_id,
    moderator.username AS assigned_moderator_username,
    moderator.id AS assigned_moderator_id,
    (EXTRACT(epoch FROM (CURRENT_TIMESTAMP - c.created_date)) / (3600)::numeric) AS hours_pending
   FROM ((public."GadukaGang_complaint" c
     JOIN public."GadukaGang_user" reporter ON ((c.reporter_id = reporter.id)))
     LEFT JOIN public."GadukaGang_user" moderator ON ((c.assigned_moderator_id = moderator.id)))
  WHERE ((c.status)::text = ANY ((ARRAY['open'::character varying, 'in_review'::character varying])::text[]))
  ORDER BY c.created_date;


--
-- Name: v_popular_tags; Type: VIEW; Schema: public; Owner: -
--

CREATE VIEW public.v_popular_tags AS
 SELECT tg.id,
    tg.name,
    tg.color,
    count(DISTINCT tt.topic_id) AS topics_count,
    count(DISTINCT t.author_id) AS unique_authors,
    COALESCE(sum(t.view_count), (0)::bigint) AS total_views,
    COALESCE(avg(t.average_rating), (0)::double precision) AS avg_rating,
    max(t.created_date) AS last_used_date
   FROM ((public."GadukaGang_tag" tg
     LEFT JOIN public."GadukaGang_topictag" tt ON ((tg.id = tt.tag_id)))
     LEFT JOIN public."GadukaGang_topic" t ON ((tt.topic_id = t.id)))
  GROUP BY tg.id, tg.name, tg.color
  ORDER BY (count(DISTINCT tt.topic_id)) DESC;


--
-- Name: v_section_statistics; Type: VIEW; Schema: public; Owner: -
--

CREATE VIEW public.v_section_statistics AS
 SELECT s.id,
    s.name,
    s.description,
    s.created_date,
    u.username AS created_by_username,
    count(DISTINCT t.id) AS topics_count,
    count(DISTINCT p.id) AS posts_count,
    count(DISTINCT t.author_id) AS unique_authors,
    max(t.created_date) AS last_topic_date,
    max(p.created_date) AS last_post_date,
    COALESCE(avg(t.view_count), (0)::numeric) AS avg_topic_views,
    COALESCE(avg(t.average_rating), (0)::double precision) AS avg_topic_rating
   FROM (((public."GadukaGang_section" s
     LEFT JOIN public."GadukaGang_user" u ON ((s.created_by_id = u.id)))
     LEFT JOIN public."GadukaGang_topic" t ON ((s.id = t.section_id)))
     LEFT JOIN public."GadukaGang_post" p ON (((t.id = p.topic_id) AND (p.is_deleted = false))))
  GROUP BY s.id, s.name, s.description, s.created_date, u.username;


--
-- Name: v_system_activity; Type: VIEW; Schema: public; Owner: -
--

CREATE VIEW public.v_system_activity AS
 SELECT sl.id,
    sl.action_type,
    sl.action_level,
    sl.description,
    sl.affected_resource_type,
    sl.affected_resource_id,
    sl."timestamp",
    u.username,
    u.role,
    date(sl."timestamp") AS activity_date,
    EXTRACT(hour FROM sl."timestamp") AS activity_hour
   FROM (public."GadukaGang_systemlog" sl
     LEFT JOIN public."GadukaGang_user" u ON ((sl.user_id = u.id)))
  ORDER BY sl."timestamp" DESC;


--
-- Name: v_top_contributors; Type: VIEW; Schema: public; Owner: -
--

CREATE VIEW public.v_top_contributors AS
 SELECT u.id,
    u.username,
    u.role,
    up.post_count,
    count(DISTINCT t.id) AS topics_count,
    COALESCE(sum(p.like_count), (0)::bigint) AS total_likes,
    COALESCE(sum(p.dislike_count), (0)::bigint) AS total_dislikes,
    count(DISTINCT ua.achievement_id) AS achievements_count,
    ur.name AS rank_name,
    rank() OVER (ORDER BY up.post_count DESC) AS post_rank
   FROM ((((((public."GadukaGang_user" u
     JOIN public."GadukaGang_userprofile" up ON ((u.id = up.user_id)))
     LEFT JOIN public."GadukaGang_topic" t ON ((u.id = t.author_id)))
     LEFT JOIN public."GadukaGang_post" p ON (((u.id = p.author_id) AND (p.is_deleted = false))))
     LEFT JOIN public."GadukaGang_userachievement" ua ON ((u.id = ua.user_id)))
     LEFT JOIN public."GadukaGang_userrankprogress" urp ON ((u.id = urp.user_id)))
     LEFT JOIN public."GadukaGang_userrank" ur ON ((urp.rank_id = ur.id)))
  WHERE (u.is_active = true)
  GROUP BY u.id, u.username, u.role, up.post_count, ur.name
  ORDER BY up.post_count DESC;


--
-- Name: v_topic_statistics; Type: VIEW; Schema: public; Owner: -
--

CREATE VIEW public.v_topic_statistics AS
 SELECT t.id,
    t.title,
    t.created_date,
    t.last_post_date,
    t.is_pinned,
    t.view_count,
    t.average_rating,
    t.rating_count,
    s.name AS section_name,
    s.id AS section_id,
    u.username AS author_username,
    u.id AS author_id,
    count(DISTINCT p.id) AS posts_count,
    count(DISTINCT p.author_id) AS unique_authors,
    count(DISTINCT tt.tag_id) AS tags_count,
    max(p.created_date) AS last_post_created,
    (EXTRACT(epoch FROM (CURRENT_TIMESTAMP - t.created_date)) / (86400)::numeric) AS age_days
   FROM ((((public."GadukaGang_topic" t
     JOIN public."GadukaGang_section" s ON ((t.section_id = s.id)))
     JOIN public."GadukaGang_user" u ON ((t.author_id = u.id)))
     LEFT JOIN public."GadukaGang_post" p ON (((t.id = p.topic_id) AND (p.is_deleted = false))))
     LEFT JOIN public."GadukaGang_topictag" tt ON ((t.id = tt.topic_id)))
  GROUP BY t.id, t.title, t.created_date, t.last_post_date, t.is_pinned, t.view_count, t.average_rating, t.rating_count, s.name, s.id, u.username, u.id;


--
-- Name: v_user_statistics; Type: VIEW; Schema: public; Owner: -
--

CREATE VIEW public.v_user_statistics AS
 SELECT u.id,
    u.username,
    u.email,
    u.role,
    u.registration_date,
    u.last_login,
    u.is_active,
    up.post_count,
    up.last_activity,
    ur.name AS rank_name,
    urp.current_points AS rank_points,
    urp.progress_percentage AS rank_progress,
    count(DISTINCT t.id) AS topics_created,
    count(DISTINCT ua.achievement_id) AS achievements_count,
    COALESCE(sum(p.like_count), (0)::bigint) AS total_likes_received,
    COALESCE(sum(p.dislike_count), (0)::bigint) AS total_dislikes_received
   FROM ((((((public."GadukaGang_user" u
     LEFT JOIN public."GadukaGang_userprofile" up ON ((u.id = up.user_id)))
     LEFT JOIN public."GadukaGang_userrankprogress" urp ON ((u.id = urp.user_id)))
     LEFT JOIN public."GadukaGang_userrank" ur ON ((urp.rank_id = ur.id)))
     LEFT JOIN public."GadukaGang_topic" t ON ((u.id = t.author_id)))
     LEFT JOIN public."GadukaGang_post" p ON (((u.id = p.author_id) AND (p.is_deleted = false))))
     LEFT JOIN public."GadukaGang_userachievement" ua ON ((u.id = ua.user_id)))
  GROUP BY u.id, u.username, u.email, u.role, u.registration_date, u.last_login, u.is_active, up.post_count, up.last_activity, ur.name, urp.current_points, urp.progress_percentage;


--
-- Name: achievements id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.achievements ALTER COLUMN id SET DEFAULT nextval('public.achievements_id_seq'::regclass);


--
-- Name: certificates id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.certificates ALTER COLUMN id SET DEFAULT nextval('public.certificates_id_seq'::regclass);


--
-- Name: chat_messages id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.chat_messages ALTER COLUMN id SET DEFAULT nextval('public.chat_messages_id_seq'::regclass);


--
-- Name: chats id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.chats ALTER COLUMN id SET DEFAULT nextval('public.chats_id_seq'::regclass);


--
-- Name: complaints id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.complaints ALTER COLUMN id SET DEFAULT nextval('public.complaints_id_seq'::regclass);


--
-- Name: forum_settings id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.forum_settings ALTER COLUMN id SET DEFAULT nextval('public.forum_settings_id_seq'::regclass);


--
-- Name: posts id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.posts ALTER COLUMN id SET DEFAULT nextval('public.posts_id_seq'::regclass);


--
-- Name: sections id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.sections ALTER COLUMN id SET DEFAULT nextval('public.sections_id_seq'::regclass);


--
-- Name: system_logs id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.system_logs ALTER COLUMN id SET DEFAULT nextval('public.system_logs_id_seq'::regclass);


--
-- Name: tags id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.tags ALTER COLUMN id SET DEFAULT nextval('public.tags_id_seq'::regclass);


--
-- Name: topics id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.topics ALTER COLUMN id SET DEFAULT nextval('public.topics_id_seq'::regclass);


--
-- Name: user_certificates id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.user_certificates ALTER COLUMN id SET DEFAULT nextval('public.user_certificates_id_seq'::regclass);


--
-- Name: user_ranks id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.user_ranks ALTER COLUMN id SET DEFAULT nextval('public.user_ranks_id_seq'::regclass);


--
-- Name: users id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.users ALTER COLUMN id SET DEFAULT nextval('public.users_id_seq'::regclass);


--
-- Data for Name: GadukaGang_achievement; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public."GadukaGang_achievement" (id, name, description, icon_url, criteria) FROM stdin;
1	Первый шаг	Создал свою первую тему на форуме. Поздравляем с началом пути!		{}
2	Завершен курс: Python для начинающих	Вы успешно завершили курс "Python для начинающих"		{"course_id": 1}
\.


--
-- Data for Name: GadukaGang_adminlog; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public."GadukaGang_adminlog" (id, action_type, description, affected_resource_type, affected_resource_id, created_date, admin_id) FROM stdin;
\.


--
-- Data for Name: GadukaGang_certificate; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public."GadukaGang_certificate" (id, name, description, template_url, criteria) FROM stdin;
2	Сертификат: Основы Python (Начальный)	Сертификат подтверждает завершение уровня "Начальный" по теме "Основы Python"		{}
3	Сертификат: Основы Python (Средний)	Сертификат подтверждает завершение уровня "Средний" по теме "Основы Python"		{}
4	Сертификат: Основы Python (Продвинутый)	Сертификат подтверждает завершение уровня "Продвинутый" по теме "Основы Python"		{}
5	Сертификат: Структуры данных (Начальный)	Сертификат подтверждает завершение уровня "Начальный" по теме "Структуры данных"		{}
6	Сертификат: Структуры данных (Средний)	Сертификат подтверждает завершение уровня "Средний" по теме "Структуры данных"		{}
7	Сертификат: Структуры данных (Продвинутый)	Сертификат подтверждает завершение уровня "Продвинутый" по теме "Структуры данных"		{}
8	Сертификат: Объектно-ориентированное программирование (Начальный)	Сертификат подтверждает завершение уровня "Начальный" по теме "Объектно-ориентированное программирование"		{}
9	Сертификат: Объектно-ориентированное программирование (Средний)	Сертификат подтверждает завершение уровня "Средний" по теме "Объектно-ориентированное программирование"		{}
10	Сертификат: Объектно-ориентированное программирование (Продвинутый)	Сертификат подтверждает завершение уровня "Продвинутый" по теме "Объектно-ориентированное программирование"		{}
11	Сертификат: Работа с файлами (Начальный)	Сертификат подтверждает завершение уровня "Начальный" по теме "Работа с файлами"		{}
12	Сертификат: Работа с файлами (Средний)	Сертификат подтверждает завершение уровня "Средний" по теме "Работа с файлами"		{}
13	Сертификат: Работа с файлами (Продвинутый)	Сертификат подтверждает завершение уровня "Продвинутый" по теме "Работа с файлами"		{}
14	Сертификат: Регулярные выражения (Начальный)	Сертификат подтверждает завершение уровня "Начальный" по теме "Регулярные выражения"		{}
15	Сертификат: Регулярные выражения (Средний)	Сертификат подтверждает завершение уровня "Средний" по теме "Регулярные выражения"		{}
16	Сертификат: Регулярные выражения (Продвинутый)	Сертификат подтверждает завершение уровня "Продвинутый" по теме "Регулярные выражения"		{}
17	Сертификат: Многопоточность (Начальный)	Сертификат подтверждает завершение уровня "Начальный" по теме "Многопоточность"		{}
18	Сертификат: Многопоточность (Средний)	Сертификат подтверждает завершение уровня "Средний" по теме "Многопоточность"		{}
19	Сертификат: Многопоточность (Продвинутый)	Сертификат подтверждает завершение уровня "Продвинутый" по теме "Многопоточность"		{}
20	Сертификат: Работа с сетью (Начальный)	Сертификат подтверждает завершение уровня "Начальный" по теме "Работа с сетью"		{}
21	Сертификат: Работа с сетью (Средний)	Сертификат подтверждает завершение уровня "Средний" по теме "Работа с сетью"		{}
22	Сертификат: Работа с сетью (Продвинутый)	Сертификат подтверждает завершение уровня "Продвинутый" по теме "Работа с сетью"		{}
23	Сертификат: Базы данных (Начальный)	Сертификат подтверждает завершение уровня "Начальный" по теме "Базы данных"		{}
24	Сертификат: Базы данных (Средний)	Сертификат подтверждает завершение уровня "Средний" по теме "Базы данных"		{}
25	Сертификат: Базы данных (Продвинутый)	Сертификат подтверждает завершение уровня "Продвинутый" по теме "Базы данных"		{}
26	Сертификат: Тестирование (Начальный)	Сертификат подтверждает завершение уровня "Начальный" по теме "Тестирование"		{}
27	Сертификат: Тестирование (Средний)	Сертификат подтверждает завершение уровня "Средний" по теме "Тестирование"		{}
28	Сертификат: Тестирование (Продвинутый)	Сертификат подтверждает завершение уровня "Продвинутый" по теме "Тестирование"		{}
29	Сертификат: Веб-разработка (Начальный)	Сертификат подтверждает завершение уровня "Начальный" по теме "Веб-разработка"		{}
30	Сертификат: Веб-разработка (Средний)	Сертификат подтверждает завершение уровня "Средний" по теме "Веб-разработка"		{}
31	Сертификат: Веб-разработка (Продвинутый)	Сертификат подтверждает завершение уровня "Продвинутый" по теме "Веб-разработка"		{}
32	Сертификат о прохождении курса: Python для начинающих	Сертификат подтверждает успешное прохождение курса "Python для начинающих"		{"course_id": 1}
\.


--
-- Data for Name: GadukaGang_chat; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public."GadukaGang_chat" (id, name, chat_type, created_date, is_active, created_by_id) FROM stdin;
\.


--
-- Data for Name: GadukaGang_chatmessage; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public."GadukaGang_chatmessage" (id, content, sent_date, is_edited, edited_date, is_deleted, chat_id, sender_id) FROM stdin;
\.


--
-- Data for Name: GadukaGang_chatparticipant; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public."GadukaGang_chatparticipant" (id, joined_date, left_date, role_in_chat, chat_id, user_id) FROM stdin;
\.


--
-- Data for Name: GadukaGang_community; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public."GadukaGang_community" (id, name, description, created_date, is_active, member_count, icon_url, is_private, creator_id, invite_token) FROM stdin;
2	Python для начинающих	asd	2025-11-23 17:22:39.095698+03	t	3	https://avatars.mds.yandex.net/i?id=00cc89b360751e4f63838f48ff9b1b0bb2acf59e-5207234-images-thumbs&n=13	t	3	xniCcUKeM6HogDaxtU8IW3_p7c07sp_td_INRRPT5jA
1	Python для начинающих	Гайды для новичков	2025-11-23 17:10:30.090849+03	t	1		f	3	\N
\.


--
-- Data for Name: GadukaGang_communitymembership; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public."GadukaGang_communitymembership" (id, joined_date, role, community_id, user_id) FROM stdin;
1	2025-11-23 17:10:30.106117+03	owner	1	3
5	2025-11-23 17:22:39.097698+03	owner	2	3
19	2025-11-24 09:04:03.284943+03	member	2	4
22	2025-11-24 10:49:29.438835+03	member	2	6
\.


--
-- Data for Name: GadukaGang_communitynotificationsubscription; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public."GadukaGang_communitynotificationsubscription" (id, notify_on_new_post, created_date, community_id, user_id) FROM stdin;
\.


--
-- Data for Name: GadukaGang_communitytopic; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public."GadukaGang_communitytopic" (id, created_date, community_id, topic_id) FROM stdin;
1	2025-11-23 19:34:04.539289+03	1	8
2	2025-11-23 19:51:59.781029+03	1	9
3	2025-11-23 20:23:02.781904+03	1	10
4	2025-11-23 20:23:04.906187+03	1	11
5	2025-11-23 20:23:05.090193+03	1	12
6	2025-11-23 20:23:05.283904+03	1	13
7	2025-11-23 20:30:45.272631+03	1	14
8	2025-11-23 20:34:59.390536+03	1	15
9	2025-11-23 20:43:57.251562+03	2	16
10	2025-11-24 07:18:19.464808+03	2	17
11	2025-11-24 07:19:42.129595+03	2	18
\.


--
-- Data for Name: GadukaGang_complaint; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public."GadukaGang_complaint" (id, target_type, target_id, reason, description, status, created_date, resolved_date, assigned_moderator_id, reporter_id) FROM stdin;
\.


--
-- Data for Name: GadukaGang_course; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public."GadukaGang_course" (id, title, description, icon_url, created_date, "order", is_active) FROM stdin;
1	Python для начинающих	Подробный курс по основам Python. Изучите переменные, типы данных, циклы и многое другое.		2025-11-23 21:33:33.718288+03	1	t
2	Python для продвинутых	Продвинутый курс по Python. Работа с алгоритмами, структурами данных и сложными задачами.		2025-11-23 22:06:31.559318+03	2	t
3	Python для профессионалов	Профессиональный курс по Python. Сложные алгоритмы, оптимизация, работа с большими данными.		2025-11-23 22:06:37.111042+03	3	t
\.


--
-- Data for Name: GadukaGang_courseprogress; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public."GadukaGang_courseprogress" (id, started_date, completed_date, is_completed, course_id, user_id) FROM stdin;
1	2025-11-23 21:34:21.032838+03	2025-11-23 21:49:28.684911+03	t	1	4
2	2025-11-23 22:07:01.865342+03	\N	f	2	4
3	2025-11-24 07:01:50.837139+03	\N	f	1	3
4	2025-11-24 08:59:49.658696+03	\N	f	2	3
\.


--
-- Data for Name: GadukaGang_courseprogress_completed_lessons; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public."GadukaGang_courseprogress_completed_lessons" (id, courseprogress_id, lesson_id) FROM stdin;
1	1	3
2	1	1
3	1	2
4	1	4
5	1	5
6	1	6
7	1	7
8	1	8
9	1	9
10	1	10
11	1	11
12	2	13
13	3	1
14	3	2
15	3	3
\.


--
-- Data for Name: GadukaGang_forumsetting; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public."GadukaGang_forumsetting" (id, setting_name, setting_value, category, last_modified, modified_by_id) FROM stdin;
\.


--
-- Data for Name: GadukaGang_githubauth; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public."GadukaGang_githubauth" (id, github_id, github_username, access_token, refresh_token, created_date, last_sync, user_id) FROM stdin;
\.


--
-- Data for Name: GadukaGang_lesson; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public."GadukaGang_lesson" (id, title, content, lesson_type, "order", created_date, practice_code_template, practice_solution, course_id, test_input, test_output, test_cases) FROM stdin;
1	Введение в Python	# Введение в Python\n\nPython — это высокоуровневый язык программирования, который известен своей простотой и читаемостью.\n\n## Что такое Python?\n\nPython был создан Гвидо ван Россумом и впервые выпущен в 1991 году. Название языка происходит от комедийного шоу "Monty Python's Flying Circus".\n\n## Преимущества Python:\n\n- **Простота**: Синтаксис Python очень понятный и похож на обычный английский язык\n- **Универсальность**: Python используется для веб-разработки, анализа данных, машинного обучения и многого другого\n- **Большое сообщество**: Множество библиотек и активное сообщество разработчиков\n\n## Ваша первая программа\n\nДавайте начнем с классической программы "Hello, World!":\n\n```python\nprint("Hello, World!")\n```\n\nЭта программа выводит текст "Hello, World!" на экран. Функция `print()` используется для вывода данных.	lecture	1	2025-11-23 21:33:33.728419+03			1			[]
2	Переменные	# Переменные в Python\n\nПеременная — это именованная область памяти, где хранятся данные.\n\n## Создание переменных\n\nВ Python переменные создаются простым присваиванием значения:\n\n```python\nname = "Иван"\nage = 25\nheight = 1.75\n```\n\n## Правила именования переменных:\n\n- Имя должно начинаться с буквы или подчеркивания\n- Может содержать буквы, цифры и подчеркивания\n- Регистр имеет значение (name и Name — разные переменные)\n- Нельзя использовать зарезервированные слова (if, for, class и т.д.)\n\n## Примеры:\n\n```python\n# Строка\nname = "Python"\n\n# Число\nnumber = 42\n\n# Дробное число\npi = 3.14\n\n# Булево значение\nis_active = True\n```	lecture	2	2025-11-23 21:33:33.730419+03			1			[]
3	Практика: Работа с переменными	# Практическое задание: Переменные\n\nСоздайте переменные для хранения информации о себе:\n- Ваше имя\n- Ваш возраст\n- Ваш любимый язык программирования\n\nЗатем выведите эту информацию на экран.	practice	3	2025-11-23 21:33:33.731419+03	# Создайте переменные здесь\nname = ""\nage = 0\nfavorite_language = ""\n\n# Выведите информацию\nprint("Имя:", name)\nprint("Возраст:", age)\nprint("Любимый язык:", favorite_language)		1			[]
4	Типы данных	# Типы данных в Python\n\nPython имеет несколько встроенных типов данных:\n\n## Основные типы:\n\n### 1. Числа (Numbers)\n- **int** — целые числа: `42`, `-10`, `0`\n- **float** — дробные числа: `3.14`, `-0.5`, `2.0`\n\n### 2. Строки (Strings)\nСтроки — это последовательности символов:\n```python\ntext = "Привет, мир!"\nmessage = 'Это тоже строка'\n```\n\n### 3. Булевы значения (Boolean)\n```python\nis_true = True\nis_false = False\n```\n\n### 4. Списки (Lists)\nСписки — это упорядоченные коллекции элементов:\n```python\nnumbers = [1, 2, 3, 4, 5]\nfruits = ["яблоко", "банан", "апельсин"]\n```\n\n### 5. Словари (Dictionaries)\nСловари хранят пары ключ-значение:\n```python\nperson = {\n    "name": "Иван",\n    "age": 25,\n    "city": "Москва"\n}\n```\n\n## Проверка типа данных\n\nИспользуйте функцию `type()` для проверки типа:\n```python\nx = 42\nprint(type(x))  # <class 'int'>\n```	lecture	4	2025-11-23 21:33:33.732421+03			1			[]
5	Вывод данных	# Вывод данных в Python\n\nФункция `print()` используется для вывода данных на экран.\n\n## Базовое использование\n\n```python\nprint("Hello, World!")\nprint(42)\nprint(3.14)\n```\n\n## Вывод нескольких значений\n\n```python\nname = "Иван"\nage = 25\nprint("Имя:", name, "Возраст:", age)\n```\n\n## Форматирование строк\n\n### 1. f-строки (рекомендуется)\n```python\nname = "Иван"\nage = 25\nprint(f"Меня зовут {name}, мне {age} лет")\n```\n\n### 2. Метод format()\n```python\nprint("Меня зовут {}, мне {} лет".format(name, age))\n```\n\n### 3. % форматирование\n```python\nprint("Меня зовут %s, мне %d лет" % (name, age))\n```\n\n## Специальные символы\n\n```python\nprint("Первая строка\\nВторая строка")  # Перевод строки\nprint("Табуляция\\tтекст")  # Табуляция\n```	lecture	5	2025-11-23 21:33:33.734421+03			1			[]
6	Практика: Вывод данных	# Практическое задание: Вывод данных\n\nСоздайте программу, которая выводит информацию о книге:\n- Название книги\n- Автор\n- Год издания\n- Количество страниц\n\nИспользуйте f-строки для форматирования вывода.	practice	6	2025-11-23 21:33:33.736422+03	# Создайте переменные для книги\nbook_title = ""\nauthor = ""\nyear = 0\npages = 0\n\n# Выведите информацию используя f-строки\nprint(f"Название: {book_title}")\nprint(f"Автор: {author}")\nprint(f"Год: {year}")\nprint(f"Страниц: {pages}")		1			[]
7	Условные операторы	# Условные операторы\n\nУсловные операторы позволяют выполнять код в зависимости от условий.\n\n## Оператор if\n\n```python\nage = 18\nif age >= 18:\n    print("Вы совершеннолетний")\n```\n\n## if-else\n\n```python\nage = 15\nif age >= 18:\n    print("Вы совершеннолетний")\nelse:\n    print("Вы несовершеннолетний")\n```\n\n## if-elif-else\n\n```python\nscore = 85\nif score >= 90:\n    print("Отлично!")\nelif score >= 70:\n    print("Хорошо!")\nelif score >= 50:\n    print("Удовлетворительно")\nelse:\n    print("Нужно подтянуть")\n```\n\n## Логические операторы\n\n- `and` — и\n- `or` — или\n- `not` — не\n\n```python\nage = 25\nhas_license = True\n\nif age >= 18 and has_license:\n    print("Можно водить машину")\n```	lecture	7	2025-11-23 21:33:33.737998+03			1			[]
8	Циклы	# Циклы в Python\n\nЦиклы позволяют выполнять код несколько раз.\n\n## Цикл for\n\nЦикл `for` используется для перебора элементов:\n\n```python\n# Перебор списка\nfruits = ["яблоко", "банан", "апельсин"]\nfor fruit in fruits:\n    print(fruit)\n```\n\n### Функция range()\n\n```python\n# Перебор чисел от 0 до 4\nfor i in range(5):\n    print(i)\n\n# От 1 до 10\nfor i in range(1, 11):\n    print(i)\n\n# С шагом 2\nfor i in range(0, 10, 2):\n    print(i)\n```\n\n## Цикл while\n\nЦикл `while` выполняется, пока условие истинно:\n\n```python\ncount = 0\nwhile count < 5:\n    print(count)\n    count += 1\n```\n\n## Управление циклами\n\n- `break` — прервать цикл\n- `continue` — перейти к следующей итерации\n\n```python\nfor i in range(10):\n    if i == 5:\n        break  # Прервать цикл\n    print(i)\n```	lecture	8	2025-11-23 21:33:33.739567+03			1			[]
9	Практика: Циклы	# Практическое задание: Циклы\n\nНапишите программу, которая:\n1. Выводит все четные числа от 0 до 20\n2. Вычисляет сумму чисел от 1 до 100\n3. Выводит таблицу умножения на 5 (от 1 до 10)	practice	9	2025-11-23 21:33:33.741645+03	# 1. Четные числа от 0 до 20\nprint("Четные числа:")\nfor i in range(0, 21, 2):\n    print(i)\n\n# 2. Сумма чисел от 1 до 100\nsum = 0\nfor i in range(1, 101):\n    sum += i\nprint(f"Сумма: {sum}")\n\n# 3. Таблица умножения на 5\nprint("Таблица умножения на 5:")\nfor i in range(1, 11):\n    print(f"5 x {i} = {5 * i}")		1			[]
10	Функции	# Функции в Python\n\nФункции позволяют группировать код для повторного использования.\n\n## Определение функции\n\n```python\ndef greet():\n    print("Привет, мир!")\n\ngreet()  # Вызов функции\n```\n\n## Функции с параметрами\n\n```python\ndef greet(name):\n    print(f"Привет, {name}!")\n\ngreet("Иван")\n```\n\n## Функции с возвращаемым значением\n\n```python\ndef add(a, b):\n    return a + b\n\nresult = add(5, 3)\nprint(result)  # 8\n```\n\n## Параметры по умолчанию\n\n```python\ndef greet(name, greeting="Привет"):\n    print(f"{greeting}, {name}!")\n\ngreet("Иван")  # Привет, Иван!\ngreet("Иван", "Здравствуй")  # Здравствуй, Иван!\n```\n\n## Локальные и глобальные переменные\n\n```python\nx = 10  # Глобальная переменная\n\ndef my_function():\n    y = 5  # Локальная переменная\n    print(x)  # Можно использовать глобальную\n    print(y)\n\nmy_function()\n```	lecture	10	2025-11-23 21:33:33.743249+03			1			[]
11	Практика: Функции	# Практическое задание: Функции\n\nСоздайте функции:\n1. `calculate_area(length, width)` — вычисляет площадь прямоугольника\n2. `is_even(number)` — проверяет, является ли число четным\n3. `factorial(n)` — вычисляет факториал числа n	practice	11	2025-11-23 21:33:33.744302+03	# 1. Функция для вычисления площади\n\ndef calculate_area(length, width):\n    # Ваш код здесь\n    pass\n\n# 2. Функция для проверки четности\n\ndef is_even(number):\n    # Ваш код здесь\n    pass\n\n# 3. Функция для вычисления факториала\n\ndef factorial(n):\n    # Ваш код здесь\n    pass\n\n# Тестирование\nprint(calculate_area(5, 3))  # Должно быть 15\nprint(is_even(4))  # Должно быть True\nprint(factorial(5))  # Должно быть 120		1			[]
12	Работа со списками и алгоритмы	# Работа со списками и алгоритмы\n\nВ этом уроке мы изучим продвинутые техники работы со списками и базовые алгоритмы.\n\n## Методы списков\n\n```python\nnumbers = [1, 2, 3, 4, 5]\nnumbers.append(6)  # Добавить элемент\nnumbers.extend([7, 8])  # Расширить список\nnumbers.insert(0, 0)  # Вставить элемент\nnumbers.remove(3)  # Удалить элемент\nnumbers.pop()  # Удалить последний элемент\n```\n\n## Сортировка\n\n```python\nnumbers = [3, 1, 4, 1, 5, 9, 2, 6]\nnumbers.sort()  # Сортировка на месте\nsorted_numbers = sorted(numbers)  # Возвращает новый список\n```\n\n## Поиск и фильтрация\n\n```python\nnumbers = [1, 2, 3, 4, 5]\nindex = numbers.index(3)  # Найти индекс элемента\nfiltered = [x for x in numbers if x > 3]  # Списочное включение\n```	lecture	1	2025-11-23 22:06:31.567421+03			2			[]
13	Практика: Сортировка и поиск	# Практическое задание: Сортировка и поиск\n\nНапишите программу, которая:\n1. Принимает список чисел через input (числа разделены пробелами)\n2. Сортирует список по убыванию\n3. Выводит отсортированный список, каждое число на новой строке\n\n**Пример входных данных:**\n```\n5 2 8 1 9 3\n```\n\n**Ожидаемый вывод:**\n```\n9\n8\n5\n3\n2\n1\n```	practice	2	2025-11-23 22:06:31.573458+03	# Введите код здесь\n# Используйте input() для получения данных\n# Числа разделены пробелами\n		2	5 2 8 1 9 3	9\n8\n5\n3\n2\n1	[]
14	Словари и множества	# Словари и множества\n\n## Словари (Dictionaries)\n\nСловари - это структуры данных типа ключ-значение.\n\n```python\nperson = {\n    "name": "Иван",\n    "age": 25,\n    "city": "Москва"\n}\n\n# Доступ к значениям\nprint(person["name"])  # Иван\nprint(person.get("age", 0))  # 25, или 0 если ключа нет\n\n# Итерация\nfor key, value in person.items():\n    print(f"{key}: {value}")\n```\n\n## Множества (Sets)\n\nМножества хранят уникальные элементы.\n\n```python\nnumbers = {1, 2, 3, 4, 5}\nnumbers.add(6)  # Добавить элемент\nnumbers.remove(3)  # Удалить элемент\n\n# Операции с множествами\nset1 = {1, 2, 3}\nset2 = {3, 4, 5}\nunion = set1 | set2  # Объединение\nintersection = set1 & set2  # Пересечение\n```	lecture	3	2025-11-23 22:06:31.578716+03			2			[]
15	Практика: Подсчет частоты элементов	# Практическое задание: Подсчет частоты элементов\n\nНапишите программу, которая:\n1. Принимает строку слов через input (слова разделены пробелами)\n2. Подсчитывает частоту каждого слова\n3. Выводит каждое слово и его частоту в формате: "слово: количество" (каждая пара на новой строке)\n4. Слова должны быть отсортированы по алфавиту\n\n**Пример входных данных:**\n```\nяблоко банан яблоко апельсин банан яблоко\n```\n\n**Ожидаемый вывод:**\n```\nапельсин: 1\nбанан: 2\nяблоко: 3\n```	practice	4	2025-11-23 22:06:31.583913+03	# Введите код здесь\n# Используйте словарь для подсчета частоты\n		2	яблоко банан яблоко апельсин банан яблоко	апельсин: 1\nбанан: 2\nяблоко: 3	[]
16	Обработка строк	# Обработка строк\n\n## Методы строк\n\n```python\ntext = "  Hello, World!  "\ntext.strip()  # Убрать пробелы с краев\ntext.upper()  # Верхний регистр\ntext.lower()  # Нижний регистр\ntext.replace("Hello", "Hi")  # Замена\ntext.split(",")  # Разделить по разделителю\n```\n\n## Форматирование\n\n```python\nname = "Иван"\nage = 25\nmessage = f"Меня зовут {name}, мне {age} лет"\n```\n\n## Работа с символами\n\n```python\ntext = "Python"\nfor char in text:\n    print(char)\n\n# Проверка\ntext.isalpha()  # Только буквы\ntext.isdigit()  # Только цифры\ntext.isalnum()  # Буквы и цифры\n```	lecture	5	2025-11-23 22:06:31.587304+03			2			[]
17	Практика: Обработка текста	# Практическое задание: Обработка текста\n\nНапишите программу, которая:\n1. Принимает строку через input\n2. Удаляет все пробелы из строки\n3. Преобразует все буквы в верхний регистр\n4. Выводит результат\n\n**Пример входных данных:**\n```\nHello World Python\n```\n\n**Ожидаемый вывод:**\n```\nHELLOWORLDPYTHON\n```	practice	6	2025-11-23 22:06:31.591509+03	# Введите код здесь\n		2	Hello World Python	HELLOWORLDPYTHON	[]
18	Рекурсия	# Рекурсия\n\nРекурсия - это техника, когда функция вызывает сама себя.\n\n## Пример: Факториал\n\n```python\ndef factorial(n):\n    if n <= 1:\n        return 1\n    return n * factorial(n - 1)\n```\n\n## Пример: Числа Фибоначчи\n\n```python\ndef fibonacci(n):\n    if n <= 1:\n        return n\n    return fibonacci(n - 1) + fibonacci(n - 2)\n```\n\n## Важно\n\n- Всегда должно быть базовое условие (когда рекурсия останавливается)\n- Рекурсия может быть неэффективной для больших значений\n- Используйте мемоизацию для оптимизации	lecture	7	2025-11-23 22:06:31.596253+03			2			[]
19	Практика: Рекурсивная сумма	# Практическое задание: Рекурсивная сумма\n\nНапишите рекурсивную функцию `sum_digits(n)`, которая:\n1. Принимает целое число n\n2. Возвращает сумму всех цифр числа\n3. Если число отрицательное, работайте с его абсолютным значением\n\nЗатем в основной программе:\n- Примите число через input\n- Вызовите функцию sum_digits\n- Выведите результат\n\n**Пример входных данных:**\n```\n12345\n```\n\n**Ожидаемый вывод:**\n```\n15\n```\n\n(1+2+3+4+5 = 15)	practice	8	2025-11-23 22:06:31.599829+03	# Введите код здесь\n# Создайте рекурсивную функцию sum_digits\n		2	12345	15	[]
20	Работа с файлами	# Работа с файлами\n\n## Чтение файлов\n\n```python\n# Чтение всего файла\nwith open('file.txt', 'r', encoding='utf-8') as f:\n    content = f.read()\n\n# Чтение построчно\nwith open('file.txt', 'r', encoding='utf-8') as f:\n    for line in f:\n        print(line.strip())\n```\n\n## Запись в файлы\n\n```python\nwith open('output.txt', 'w', encoding='utf-8') as f:\n    f.write("Hello, World!")\n```\n\n## Режимы открытия\n\n- `'r'` - чтение\n- `'w'` - запись (перезапись)\n- `'a'` - добавление\n- `'r+'` - чтение и запись	lecture	9	2025-11-23 22:06:31.603883+03			2			[]
21	Практика: Обработка данных	# Практическое задание: Обработка данных\n\nНапишите программу, которая:\n1. Принимает через input список чисел, разделенных пробелами\n2. Находит максимальное и минимальное значение\n3. Вычисляет среднее арифметическое (округлить до 2 знаков после запятой)\n4. Выводит результат в формате:\n   ```\n   Максимум: <макс>\n   Минимум: <мин>\n   Среднее: <среднее>\n   ```\n\n**Пример входных данных:**\n```\n10 20 30 40 50\n```\n\n**Ожидаемый вывод:**\n```\nМаксимум: 50\nМинимум: 10\nСреднее: 30.0\n```	practice	10	2025-11-23 22:06:31.609255+03	# Введите код здесь\n		2	10 20 30 40 50	Максимум: 50\nМинимум: 10\nСреднее: 30.0	[]
22	Алгоритмы сортировки	# Алгоритмы сортировки\n\n## Быстрая сортировка (Quick Sort)\n\nБыстрая сортировка использует стратегию "разделяй и властвуй".\n\n```python\ndef quicksort(arr):\n    if len(arr) <= 1:\n        return arr\n    pivot = arr[len(arr) // 2]\n    left = [x for x in arr if x < pivot]\n    middle = [x for x in arr if x == pivot]\n    right = [x for x in arr if x > pivot]\n    return quicksort(left) + middle + quicksort(right)\n```\n\n## Сортировка слиянием (Merge Sort)\n\n```python\ndef merge_sort(arr):\n    if len(arr) <= 1:\n        return arr\n    mid = len(arr) // 2\n    left = merge_sort(arr[:mid])\n    right = merge_sort(arr[mid:])\n    return merge(left, right)\n\ndef merge(left, right):\n    result = []\n    i = j = 0\n    while i < len(left) and j < len(right):\n        if left[i] <= right[j]:\n            result.append(left[i])\n            i += 1\n        else:\n            result.append(right[j])\n            j += 1\n    result.extend(left[i:])\n    result.extend(right[j:])\n    return result\n```	lecture	1	2025-11-23 22:06:37.125362+03			3			[]
23	Практика: Реализация быстрой сортировки	# Практическое задание: Реализация быстрой сортировки\n\nРеализуйте алгоритм быстрой сортировки для сортировки списка чисел по возрастанию.\n\nПрограмма должна:\n1. Принимать список чисел через input (числа разделены пробелами)\n2. Сортировать числа по возрастанию используя быструю сортировку\n3. Выводить отсортированный список, числа разделены пробелами\n\n**Пример входных данных:**\n```\n64 34 25 12 22 11 90\n```\n\n**Ожидаемый вывод:**\n```\n11 12 22 25 34 64 90\n```	practice	2	2025-11-23 22:06:37.132109+03	# Введите код здесь\n# Реализуйте функцию быстрой сортировки\n		3	64 34 25 12 22 11 90	11 12 22 25 34 64 90	[]
24	Поиск в графах	# Поиск в графах\n\n## Поиск в глубину (DFS)\n\n```python\ndef dfs(graph, start, visited=None):\n    if visited is None:\n        visited = set()\n    visited.add(start)\n    print(start)\n    for neighbor in graph[start]:\n        if neighbor not in visited:\n            dfs(graph, neighbor, visited)\n```\n\n## Поиск в ширину (BFS)\n\n```python\nfrom collections import deque\n\ndef bfs(graph, start):\n    visited = set()\n    queue = deque([start])\n    visited.add(start)\n    while queue:\n        node = queue.popleft()\n        print(node)\n        for neighbor in graph[node]:\n            if neighbor not in visited:\n                visited.add(neighbor)\n                queue.append(neighbor)\n```	lecture	3	2025-11-23 22:06:37.136242+03			3			[]
25	Практика: Поиск кратчайшего пути	# Практическое задание: Поиск кратчайшего пути\n\nНапишите программу, которая находит кратчайший путь между двумя узлами в графе.\n\nВходные данные:\n- Первая строка: количество узлов n\n- Следующие n строк: для каждого узла список соседей (индексы разделены пробелами, индексация с 0)\n- Последняя строка: начальный и конечный узел (разделены пробелом)\n\nВыведите последовательность узлов кратчайшего пути, разделенных пробелами.\n\n**Пример входных данных:**\n```\n5\n1 2\n0 2 3\n0 1 4\n1 4\n2 3\n0 4\n```\n\n**Ожидаемый вывод:**\n```\n0 1 3 4\n```	practice	4	2025-11-23 22:06:37.140487+03	# Введите код здесь\n# Реализуйте BFS для поиска кратчайшего пути\n		3	5\n1 2\n0 2 3\n0 1 4\n1 4\n2 3\n0 4	0 1 3 4	[]
26	Динамическое программирование	# Динамическое программирование\n\nДинамическое программирование - это техника решения задач путем разбиения их на подзадачи.\n\n## Задача о рюкзаке\n\n```python\ndef knapsack(weights, values, capacity):\n    n = len(weights)\n    dp = [[0 for _ in range(capacity + 1)] for _ in range(n + 1)]\n    \n    for i in range(1, n + 1):\n        for w in range(1, capacity + 1):\n            if weights[i-1] <= w:\n                dp[i][w] = max(\n                    dp[i-1][w],\n                    dp[i-1][w-weights[i-1]] + values[i-1]\n                )\n            else:\n                dp[i][w] = dp[i-1][w]\n    \n    return dp[n][capacity]\n```\n\n## Числа Фибоначчи с мемоизацией\n\n```python\ndef fibonacci_memo(n, memo={}):\n    if n in memo:\n        return memo[n]\n    if n <= 1:\n        return n\n    memo[n] = fibonacci_memo(n-1, memo) + fibonacci_memo(n-2, memo)\n    return memo[n]\n```	lecture	5	2025-11-23 22:06:37.14507+03			3			[]
27	Практика: Задача о рюкзаке	# Практическое задание: Задача о рюкзаке\n\nРеализуйте решение задачи о рюкзаке (0/1).\n\nВходные данные:\n- Первая строка: количество предметов n и вместимость рюкзака W (разделены пробелом)\n- Следующие n строк: вес и стоимость предмета (разделены пробелом)\n\nВыведите максимальную стоимость, которую можно унести в рюкзаке.\n\n**Пример входных данных:**\n```\n3 50\n10 60\n20 100\n30 120\n```\n\n**Ожидаемый вывод:**\n```\n220\n```	practice	6	2025-11-23 22:06:37.14907+03	# Введите код здесь\n# Реализуйте решение задачи о рюкзаке\n		3	3 50\n10 60\n20 100\n30 120	220	[]
28	Обработка больших данных	# Обработка больших данных\n\n## Генераторы\n\nГенераторы позволяют создавать последовательности без хранения всех элементов в памяти.\n\n```python\ndef fibonacci_generator():\n    a, b = 0, 1\n    while True:\n        yield a\n        a, b = b, a + b\n\n# Использование\nfib = fibonacci_generator()\nfor i in range(10):\n    print(next(fib))\n```\n\n## Генераторные выражения\n\n```python\nsquares = (x**2 for x in range(10))\nsum_squares = sum(squares)\n```\n\n## Обработка потоков данных\n\n```python\ndef process_stream(stream):\n    for chunk in stream:\n        yield process_chunk(chunk)\n```	lecture	7	2025-11-23 22:06:37.153307+03			3			[]
29	Практика: Генератор простых чисел	# Практическое задание: Генератор простых чисел\n\nСоздайте генератор, который генерирует простые числа.\n\nПрограмма должна:\n1. Принимать число n через input\n2. Генерировать первые n простых чисел\n3. Выводить их, разделенные пробелами\n\n**Пример входных данных:**\n```\n10\n```\n\n**Ожидаемый вывод:**\n```\n2 3 5 7 11 13 17 19 23 29\n```	practice	8	2025-11-23 22:06:37.156895+03	# Введите код здесь\n# Создайте генератор простых чисел\n		3	10	2 3 5 7 11 13 17 19 23 29	[]
30	Оптимизация производительности	# Оптимизация производительности\n\n## Профилирование кода\n\n```python\nimport cProfile\nimport pstats\n\ndef my_function():\n    # ваш код\n    pass\n\ncProfile.run('my_function()')\n```\n\n## Кэширование\n\n```python\nfrom functools import lru_cache\n\n@lru_cache(maxsize=None)\ndef expensive_function(n):\n    # сложные вычисления\n    return result\n```\n\n## Использование встроенных функций\n\nВстроенные функции Python часто быстрее, чем циклы:\n\n```python\n# Медленно\nresult = []\nfor x in range(1000):\n    result.append(x * 2)\n\n# Быстро\nresult = [x * 2 for x in range(1000)]\n```	lecture	9	2025-11-23 22:06:37.161939+03			3			[]
31	Практика: Оптимизированная обработка	# Практическое задание: Оптимизированная обработка\n\nНапишите программу, которая:\n1. Принимает список чисел через input (числа разделены пробелами)\n2. Находит все числа, которые являются квадратами других чисел в списке\n3. Выводит найденные числа, отсортированные по возрастанию, разделенные пробелами\n4. Если таких чисел нет, выведите "Нет"\n\n**Пример входных данных:**\n```\n1 2 3 4 5 9 16 25\n```\n\n**Ожидаемый вывод:**\n```\n4 9 16 25\n```\n\n(4=2², 9=3², 16=4², 25=5²)	practice	10	2025-11-23 22:06:37.165703+03	# Введите код здесь\n# Оптимизируйте решение\n		3	1 2 3 4 5 9 16 25	4 9 16 25	[]
\.


--
-- Data for Name: GadukaGang_moderatoraction; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public."GadukaGang_moderatoraction" (id, action_type, description, target_type, target_id, created_date, moderator_id) FROM stdin;
\.


--
-- Data for Name: GadukaGang_notification; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public."GadukaGang_notification" (id, notification_type, title, message, is_read, created_date, related_resource_type, related_resource_id, user_id) FROM stdin;
\.


--
-- Data for Name: GadukaGang_post; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public."GadukaGang_post" (id, content, created_date, last_edited_date, edit_count, is_deleted, topic_id, author_id, dislike_count, like_count) FROM stdin;
4	Согласен полностью	2025-11-20 11:12:34.672026+03	\N	0	t	2	3	0	1
2	Новое сообщение для второй темы. Надеюсь вы наслаждаетесь сайтом	2025-11-17 11:38:16.554078+03	\N	0	t	2	4	0	0
7	# Привет! 👋\r\n\r\nЭто пример сообщения, оформленного в Markdown.\r\n\r\n- Можно выделять текст курсивом (*курсив* или _курсив_)\r\n- **Можно сделать текст жирным** (**жирный** или __жирный__)\r\n- Добавлять [ссылки](https://doka.guide/tools/markdown/)\r\n- Вставлять блоки кода:\r\n    ```\r\n    print("Hello, World!")\r\n    ```\r\n- Оформлять списки:\r\n    - Первый пункт\r\n    - Второй пункт\r\n    - Третий пункт\r\n- > А еще можно делать цитаты!\r\n\r\n~~Можно зачеркнуть текст~~ с помощью двойной тильды.\r\n\r\n---\r\n\r\nЕсли нужно больше примеров или конкретный сценарий — дай знать!	2025-11-22 14:42:29.79673+03	2025-11-23 13:26:41.746759+03	1	f	5	3	0	0
8	Содержание	2025-11-23 19:34:04.52629+03	\N	0	f	8	4	0	0
9	привет	2025-11-23 19:51:59.772308+03	\N	0	f	9	4	0	0
10	Новая тема	2025-11-23 20:23:02.772862+03	\N	0	f	10	4	0	0
11	Новая тема	2025-11-23 20:23:04.897186+03	\N	0	f	11	4	0	0
12	Новая тема	2025-11-23 20:23:05.081192+03	\N	0	f	12	4	0	0
13	Новая тема	2025-11-23 20:23:05.276904+03	\N	0	f	13	4	0	0
14	Тема	2025-11-23 20:30:45.261496+03	\N	0	f	14	4	0	0
15	тема	2025-11-23 20:34:59.380621+03	\N	0	f	15	3	0	0
16	тема приват	2025-11-23 20:43:57.241987+03	\N	0	f	16	4	0	0
17	привет	2025-11-24 01:46:53.69557+03	\N	0	f	16	3	0	0
18	asd	2025-11-24 07:18:19.422458+03	\N	0	t	17	3	0	0
19	фыв	2025-11-24 07:19:42.105943+03	\N	0	f	18	4	0	0
1	Это первая тема. Как вам?	2025-11-13 12:59:30.125161+03	\N	0	f	1	4	0	1
3	qwe	2025-11-17 12:41:35.388403+03	\N	0	f	3	3	0	0
\.


--
-- Data for Name: GadukaGang_postlike; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public."GadukaGang_postlike" (id, like_type, created_date, post_id, user_id) FROM stdin;
9	like	2025-11-17 11:31:25.665927+03	1	3
21	dislike	2025-11-20 22:45:41.660226+03	4	3
\.


--
-- Data for Name: GadukaGang_searchindex; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public."GadukaGang_searchindex" (id, content_type, object_id, search_vector, tags, author_username, created_date, last_updated) FROM stdin;
\.


--
-- Data for Name: GadukaGang_section; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public."GadukaGang_section" (id, name, description, created_date, created_by_id) FROM stdin;
1	Django и веб	Веб-разработка именно на Django/Django REST, FastAPI, интеграции с фронтом.	2025-11-13 12:57:01.062679+03	3
2	Data Science	NumPy, Pandas, scikit-learn, PyTorch, обработка данных, аналитика.	2025-11-13 12:57:15.291564+03	3
3	Автоматизация и DevOps	Скрипты на Python, Ansible, CI/CD, тесты, инфраструктура.	2025-11-13 12:57:34.925538+03	3
4	Основы языка	Синтаксис, стандартная библиотека, best practices, вопросы для новичков.	2025-11-13 12:57:46.762162+03	3
5	Карьера Python-разработчика	Резюме, собеседования, развитие навыков, рабочие кейсы.	2025-11-13 12:57:59.474441+03	3
6	Сообщества	Темы из сообществ	2025-11-24 07:18:19.399482+03	\N
\.


--
-- Data for Name: GadukaGang_systemlog; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public."GadukaGang_systemlog" (id, action_type, action_level, description, affected_resource_type, affected_resource_id, "timestamp", user_id) FROM stdin;
1	post_deleted	user	Пост #4 помечен как удалённый	post	4	2025-11-22 23:25:51.746028+03	3
2	post_deleted	user	Пост #2 помечен как удалённый	post	2	2025-11-22 23:26:00.862226+03	4
3	post_edited	user	Пост #7 отредактирован (редакция #1)	post	7	2025-11-23 13:26:41.74814+03	3
4	achievement_earned	user	Получено достижение #1	achievement	1	2025-11-23 17:12:30.738408+03	4
5	achievement_earned	user	Получено достижение #2	achievement	2	2025-11-23 21:49:28.693119+03	4
6	post_deleted	user	Пост #18 помечен как удалённый	post	18	2025-11-24 07:18:57.657245+03	3
7	role_changed	moderator	Роль изменена с "user" на "moderator"	user	4	2025-11-24 10:19:49.198145+03	4
8	role_changed	user	Роль изменена с "moderator" на "user"	user	4	2025-11-24 10:20:22.141604+03	4
9	role_changed	moderator	Роль изменена с "user" на "moderator"	user	3	2025-11-24 10:20:48.626841+03	3
\.


--
-- Data for Name: GadukaGang_tag; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public."GadukaGang_tag" (id, name, color) FROM stdin;
1	Python	#3776ab
2	Django	#092e20
3	JavaScript	#f7df1e
4	HTML	#e34f26
5	CSS	#1572b6
6	Базы данных	#4479a1
7	SQL	#e38c00
8	PostgreSQL	#336791
9	Веб-разработка	#20c20e
10	Фронтенд	#ff6b6b
11	Бэкенд	#4ecdc4
12	API	#ff9f1c
13	Аутентификация	#6a0572
14	Безопасность	#ff0000
15	Оптимизация	#00b894
16	Тестирование	#0984e3
17	Отладка	#6c5ce7
18	Docker	#0db7ed
19	Git	#f05032
20	Алгоритмы	#a29bfe
\.


--
-- Data for Name: GadukaGang_topic; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public."GadukaGang_topic" (id, title, created_date, last_post_date, is_pinned, view_count, section_id, author_id, average_rating, rating_count) FROM stdin;
17	asd	2025-11-24 07:18:19.413259+03	2025-11-24 07:18:19.422458+03	f	1	6	3	0	0
18	тема	2025-11-24 07:19:42.094416+03	2025-11-24 07:19:42.105943+03	f	2	6	4	0	0
16	тема приват	2025-11-23 20:43:57.238812+03	2025-11-24 01:46:53.783284+03	f	3	1	4	0	0
3	Первая тема!	2025-11-17 12:41:35.377327+03	2025-11-21 20:13:20.305193+03	f	17	2	3	0	0
2	Вторая тема	2025-11-17 11:38:16.531551+03	2025-11-20 11:12:34.701978+03	f	21	2	4	4.5	2
1	Первая тема!	2025-11-13 12:59:30.096637+03	2025-11-22 11:46:15.545915+03	f	50	2	4	5	2
5	Тест markdown	2025-11-22 14:42:29.789943+03	2025-11-22 14:42:29.79673+03	f	2	1	3	0	0
6	Первая тема первого сообщества	2025-11-23 17:12:30.724269+03	2025-11-23 17:12:30.724269+03	f	2	1	4	0	0
7	Первая тема первого сообщества	2025-11-23 18:42:26.539982+03	2025-11-23 18:42:26.539982+03	f	0	1	3	0	0
8	Новая тема	2025-11-23 19:34:04.518128+03	2025-11-23 19:34:04.52629+03	f	1	1	4	0	0
10	Новая тема	2025-11-23 20:23:02.762457+03	2025-11-23 20:23:02.772862+03	f	0	1	4	0	0
11	Новая тема	2025-11-23 20:23:04.89506+03	2025-11-23 20:23:04.897186+03	f	0	1	4	0	0
13	Новая тема	2025-11-23 20:23:05.274328+03	2025-11-23 20:23:05.276904+03	f	1	1	4	0	0
14	Тема	2025-11-23 20:30:45.25939+03	2025-11-23 20:30:45.261496+03	f	1	1	4	0	0
15	тема	2025-11-23 20:34:59.371947+03	2025-11-23 20:34:59.380621+03	f	1	1	3	0	0
9	Тема	2025-11-23 19:51:59.770305+03	2025-11-23 19:51:59.772308+03	f	2	1	4	0	0
12	Новая тема	2025-11-23 20:23:05.079192+03	2025-11-23 20:23:05.081192+03	f	1	1	4	0	0
\.


--
-- Data for Name: GadukaGang_topicrating; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public."GadukaGang_topicrating" (id, rating, created_date, topic_id, user_id) FROM stdin;
1	5	2025-11-17 11:11:21.707425+03	1	4
2	5	2025-11-17 12:13:13.330446+03	2	4
3	4	2025-11-17 12:16:48.050469+03	2	3
4	5	2025-11-17 12:17:43.613668+03	1	3
\.


--
-- Data for Name: GadukaGang_topicsubscription; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public."GadukaGang_topicsubscription" (id, created_date, notify_on_new_post, topic_id, user_id) FROM stdin;
\.


--
-- Data for Name: GadukaGang_topictag; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public."GadukaGang_topictag" (id, tag_id, topic_id) FROM stdin;
4	9	2
5	10	3
8	1	5
9	6	5
10	7	5
11	10	5
12	11	5
13	12	5
14	15	5
15	16	5
16	19	5
17	1	6
\.


--
-- Data for Name: GadukaGang_topicview; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public."GadukaGang_topicview" (id, view_date, topic_id, user_id) FROM stdin;
1	2025-11-17 12:12:58.337459+03	2	4
2	2025-11-22 23:25:39.900139+03	2	3
4	2025-11-23 12:36:36.852829+03	3	3
3	2025-11-23 12:36:48.796228+03	1	3
6	2025-11-23 13:26:03.195994+03	5	3
7	2025-11-23 17:12:30.92598+03	6	4
8	2025-11-23 18:13:25.594586+03	6	3
9	2025-11-23 19:34:04.598918+03	8	4
10	2025-11-23 19:51:59.939136+03	9	4
11	2025-11-23 20:23:10.066685+03	13	4
12	2025-11-23 20:30:45.350443+03	14	4
13	2025-11-23 20:34:59.446707+03	15	3
14	2025-11-23 20:35:07.02527+03	9	3
15	2025-11-23 20:44:01.237434+03	16	4
16	2025-11-23 21:15:31.27113+03	12	4
17	2025-11-24 01:46:44.770813+03	16	3
18	2025-11-24 07:18:29.973482+03	17	3
19	2025-11-24 07:19:51.02646+03	18	4
20	2025-11-24 09:00:00.961225+03	18	3
21	2025-11-24 10:49:51.09692+03	3	6
\.


--
-- Data for Name: GadukaGang_user; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public."GadukaGang_user" (id, password, is_superuser, username, first_name, last_name, email, is_staff, date_joined, role, registration_date, last_login, is_active) FROM stdin;
1	pbkdf2_sha256$1000000$MEMF0bFjdnHC88bIZGfG1z$6SjNyh/ly4I50kDlH2+xAo7XExTv/2Ucr0ZBWDA5U50=	t	eclipse			simernin.mat@gmail.com	t	2025-09-28 15:18:31.822724+03	user	2025-09-28 15:18:32.09233+03	\N	t
3	pbkdf2_sha256$1000000$SaYiLCKFky7aZJ9WKXpyJC$cBTcA8YFeWvDCSqr7aEdLsWS5YB/HnAyatzqncN2cBs=	t	Eclipse	Матвей		simernin.mat@gmail.com	t	2025-11-10 11:03:35.662454+03	moderator	2025-11-10 11:03:36.298145+03	2025-11-24 10:48:08.232336+03	t
6	pbkdf2_sha256$1000000$U7zUcg9cdUdvcvb1deNDQu$T+ckGFZWdtbus8vUFtiNJjWJL9Ks6ycelxVqlCtW6aw=	t	superadmin			isip_m.h.simernin@mpt.com	t	2025-11-24 10:16:58.791987+03	user	2025-11-24 10:16:59.064677+03	2025-11-24 10:49:01.839806+03	t
5		f	admin_test			admin_test@gmail.com	f	2025-11-23 10:58:19.641627+03	super_admin	2025-11-23 10:58:19.641627+03	2025-11-23 10:56:55.772+03	t
2	pbkdf2_sha256$1000000$cQJpgZxnNqi381pNAcea5a$J8JqIv510L6/zinIIliFSN3UndcJID+rHMmS9BmISGE=	f	User	User	Userov	user@gmail.com	f	2025-09-28 15:37:21.173399+03	user	2025-09-28 15:37:21.49825+03	2025-10-06 11:31:08.072675+03	t
4	pbkdf2_sha256$1000000$dkt25Zclye1RClXPXi2BAU$j3AUzn26e8Lo2qROJgS/LJ85VtSAzIzkJRTHvd+3m6w=	f	RamKa			eola5173@gmail.com	f	2025-11-13 12:58:49.062894+03	user	2025-11-13 12:58:49.872745+03	2025-11-24 09:03:19.408476+03	t
\.


--
-- Data for Name: GadukaGang_user_groups; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public."GadukaGang_user_groups" (id, user_id, group_id) FROM stdin;
\.


--
-- Data for Name: GadukaGang_user_user_permissions; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public."GadukaGang_user_user_permissions" (id, user_id, permission_id) FROM stdin;
\.


--
-- Data for Name: GadukaGang_userachievement; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public."GadukaGang_userachievement" (id, earned_date, achievement_id, awarded_by_id, user_id) FROM stdin;
1	2025-11-17 12:41:35.413696+03	1	\N	3
2	2025-11-23 17:12:30.73817+03	1	\N	4
3	2025-11-23 21:49:28.692172+03	2	\N	4
\.


--
-- Data for Name: GadukaGang_usercertificate; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public."GadukaGang_usercertificate" (id, awarded_date, expiration_date, certificate_id, awarded_by_id, user_id) FROM stdin;
1	2025-11-23 21:49:28.702847+03	\N	32	\N	4
\.


--
-- Data for Name: GadukaGang_userprofile; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public."GadukaGang_userprofile" (user_id, avatar_url, bio, signature, post_count, join_date, last_activity) FROM stdin;
4				10	2025-11-13 12:58:49.886891+03	2025-11-24 07:19:42.106599+03
3				4	2025-11-11 11:20:05.749196+03	2025-11-24 07:18:57.657245+03
1				0	2025-11-17 12:27:06.577709+03	2025-11-22 11:46:15.547133+03
6				0	2025-11-24 10:37:38.946371+03	2025-11-24 10:37:38.946371+03
5				0	2025-11-23 12:34:55.518263+03	2025-11-23 12:34:55.518263+03
2		I am the first user of this system	By user	0	2025-09-28 15:37:21.501249+03	2025-09-28 16:27:36.755839+03
\.


--
-- Data for Name: GadukaGang_userrank; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public."GadukaGang_userrank" (id, name, required_points, icon_url) FROM stdin;
1	первый	1	https://w7.pngwing.com/pngs/521/763/png-transparent-1st-green-badge.png
\.


--
-- Data for Name: GadukaGang_userrankprogress; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public."GadukaGang_userrankprogress" (user_id, current_points, progress_percentage, rank_id) FROM stdin;
3	10	0	\N
4	20	0	\N
\.


--
-- Data for Name: GadukaGang_usersubscription; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public."GadukaGang_usersubscription" (id, created_date, subscribed_to_id, subscriber_id) FROM stdin;
\.


--
-- Data for Name: account_emailaddress; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.account_emailaddress (id, email, verified, "primary", user_id) FROM stdin;
1	simernin.mat@gmail.com	t	f	3
\.


--
-- Data for Name: account_emailconfirmation; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.account_emailconfirmation (id, created, sent, key, email_address_id) FROM stdin;
\.


--
-- Data for Name: achievements; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.achievements (id, name, description, icon_url, criteria) FROM stdin;
1	Первое сообщение	Написать первое сообщение на форуме	/static/images/achievements/first-post.png	{"type": "post_count", "value": 1}
2	Активный участник	Написать 50 сообщений	/static/images/achievements/active.png	{"type": "post_count", "value": 50}
3	Эксперт по Python	Получить 100 положительных оценок	/static/images/achievements/python-expert.png	{"type": "upvotes", "value": 100}
4	Помощник	Помочь 20 пользователям	/static/images/achievements/helper.png	{"type": "helped_users", "value": 20}
\.


--
-- Data for Name: auth_group; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.auth_group (id, name) FROM stdin;
\.


--
-- Data for Name: auth_group_permissions; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.auth_group_permissions (id, group_id, permission_id) FROM stdin;
\.


--
-- Data for Name: auth_permission; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.auth_permission (id, name, content_type_id, codename) FROM stdin;
1	Can add log entry	1	add_logentry
2	Can change log entry	1	change_logentry
3	Can delete log entry	1	delete_logentry
4	Can view log entry	1	view_logentry
5	Can add permission	2	add_permission
6	Can change permission	2	change_permission
7	Can delete permission	2	delete_permission
8	Can view permission	2	view_permission
9	Can add group	3	add_group
10	Can change group	3	change_group
11	Can delete group	3	delete_group
12	Can view group	3	view_group
13	Can add content type	4	add_contenttype
14	Can change content type	4	change_contenttype
15	Can delete content type	4	delete_contenttype
16	Can view content type	4	view_contenttype
17	Can add session	5	add_session
18	Can change session	5	change_session
19	Can delete session	5	delete_session
20	Can view session	5	view_session
21	Can add achievement	6	add_achievement
22	Can change achievement	6	change_achievement
23	Can delete achievement	6	delete_achievement
24	Can view achievement	6	view_achievement
25	Can add certificate	7	add_certificate
26	Can change certificate	7	change_certificate
27	Can delete certificate	7	delete_certificate
28	Can view certificate	7	view_certificate
29	Can add chat	8	add_chat
30	Can change chat	8	change_chat
31	Can delete chat	8	delete_chat
32	Can view chat	8	view_chat
33	Can add section	9	add_section
34	Can change section	9	change_section
35	Can delete section	9	delete_section
36	Can view section	9	view_section
37	Can add tag	10	add_tag
38	Can change tag	10	change_tag
39	Can delete tag	10	delete_tag
40	Can view tag	10	view_tag
41	Can add user	11	add_user
42	Can change user	11	change_user
43	Can delete user	11	delete_user
44	Can view user	11	view_user
45	Can add user rank	12	add_userrank
46	Can change user rank	12	change_userrank
47	Can delete user rank	12	delete_userrank
48	Can view user rank	12	view_userrank
49	Can add topic	13	add_topic
50	Can change topic	13	change_topic
51	Can delete topic	13	delete_topic
52	Can view topic	13	view_topic
53	Can add user profile	14	add_userprofile
54	Can change user profile	14	change_userprofile
55	Can delete user profile	14	delete_userprofile
56	Can view user profile	14	view_userprofile
57	Can add user certificate	15	add_usercertificate
58	Can change user certificate	15	change_usercertificate
59	Can delete user certificate	15	delete_usercertificate
60	Can view user certificate	15	view_usercertificate
61	Can add system log	16	add_systemlog
62	Can change system log	16	change_systemlog
63	Can delete system log	16	delete_systemlog
64	Can view system log	16	view_systemlog
65	Can add post	17	add_post
66	Can change post	17	change_post
67	Can delete post	17	delete_post
68	Can view post	17	view_post
69	Can add forum setting	18	add_forumsetting
70	Can change forum setting	18	change_forumsetting
71	Can delete forum setting	18	delete_forumsetting
72	Can view forum setting	18	view_forumsetting
73	Can add complaint	19	add_complaint
74	Can change complaint	19	change_complaint
75	Can delete complaint	19	delete_complaint
76	Can view complaint	19	view_complaint
77	Can add chat message	20	add_chatmessage
78	Can change chat message	20	change_chatmessage
79	Can delete chat message	20	delete_chatmessage
80	Can view chat message	20	view_chatmessage
81	Can add topic tag	21	add_topictag
82	Can change topic tag	21	change_topictag
83	Can delete topic tag	21	delete_topictag
84	Can view topic tag	21	view_topictag
85	Can add user rank progress	22	add_userrankprogress
86	Can change user rank progress	22	change_userrankprogress
87	Can delete user rank progress	22	delete_userrankprogress
88	Can view user rank progress	22	view_userrankprogress
89	Can add user achievement	23	add_userachievement
90	Can change user achievement	23	change_userachievement
91	Can delete user achievement	23	delete_userachievement
92	Can view user achievement	23	view_userachievement
93	Can add chat participant	24	add_chatparticipant
94	Can change chat participant	24	change_chatparticipant
95	Can delete chat participant	24	delete_chatparticipant
96	Can view chat participant	24	view_chatparticipant
97	Can add admin log	25	add_adminlog
98	Can change admin log	25	change_adminlog
99	Can delete admin log	25	delete_adminlog
100	Can view admin log	25	view_adminlog
101	Can add git hub auth	26	add_githubauth
102	Can change git hub auth	26	change_githubauth
103	Can delete git hub auth	26	delete_githubauth
104	Can view git hub auth	26	view_githubauth
105	Can add moderator action	27	add_moderatoraction
106	Can change moderator action	27	change_moderatoraction
107	Can delete moderator action	27	delete_moderatoraction
108	Can view moderator action	27	view_moderatoraction
109	Can add notification	28	add_notification
110	Can change notification	28	change_notification
111	Can delete notification	28	delete_notification
112	Can view notification	28	view_notification
113	Can add search index	29	add_searchindex
114	Can change search index	29	change_searchindex
115	Can delete search index	29	delete_searchindex
116	Can view search index	29	view_searchindex
117	Can add post like	30	add_postlike
118	Can change post like	30	change_postlike
119	Can delete post like	30	delete_postlike
120	Can view post like	30	view_postlike
121	Can add topic rating	31	add_topicrating
122	Can change topic rating	31	change_topicrating
123	Can delete topic rating	31	delete_topicrating
124	Can view topic rating	31	view_topicrating
125	Can add topic subscription	32	add_topicsubscription
126	Can change topic subscription	32	change_topicsubscription
127	Can delete topic subscription	32	delete_topicsubscription
128	Can view topic subscription	32	view_topicsubscription
129	Can add user subscription	33	add_usersubscription
130	Can change user subscription	33	change_usersubscription
131	Can delete user subscription	33	delete_usersubscription
132	Can view user subscription	33	view_usersubscription
133	Can add site	34	add_site
134	Can change site	34	change_site
135	Can delete site	34	delete_site
136	Can view site	34	view_site
137	Can add email address	35	add_emailaddress
138	Can change email address	35	change_emailaddress
139	Can delete email address	35	delete_emailaddress
140	Can view email address	35	view_emailaddress
141	Can add email confirmation	36	add_emailconfirmation
142	Can change email confirmation	36	change_emailconfirmation
143	Can delete email confirmation	36	delete_emailconfirmation
144	Can view email confirmation	36	view_emailconfirmation
145	Can add social account	37	add_socialaccount
146	Can change social account	37	change_socialaccount
147	Can delete social account	37	delete_socialaccount
148	Can view social account	37	view_socialaccount
149	Can add social application	38	add_socialapp
150	Can change social application	38	change_socialapp
151	Can delete social application	38	delete_socialapp
152	Can view social application	38	view_socialapp
153	Can add social application token	39	add_socialtoken
154	Can change social application token	39	change_socialtoken
155	Can delete social application token	39	delete_socialtoken
156	Can view social application token	39	view_socialtoken
157	Can add topic view	40	add_topicview
158	Can change topic view	40	change_topicview
159	Can delete topic view	40	delete_topicview
160	Can view topic view	40	view_topicview
161	Can add practice topic	41	add_practicetopic
162	Can change practice topic	41	change_practicetopic
163	Can delete practice topic	41	delete_practicetopic
164	Can view practice topic	41	view_practicetopic
165	Can add user practice progress	42	add_userpracticeprogress
166	Can change user practice progress	42	change_userpracticeprogress
167	Can delete user practice progress	42	delete_userpracticeprogress
168	Can view user practice progress	42	view_userpracticeprogress
169	Can add practice level	43	add_practicelevel
170	Can change practice level	43	change_practicelevel
171	Can delete practice level	43	delete_practicelevel
172	Can view practice level	43	view_practicelevel
173	Can add Token	44	add_token
174	Can change Token	44	change_token
175	Can delete Token	44	delete_token
176	Can view Token	44	view_token
177	Can add token	45	add_tokenproxy
178	Can change token	45	change_tokenproxy
179	Can delete token	45	delete_tokenproxy
180	Can view token	45	view_tokenproxy
181	Can add community topic	46	add_communitytopic
182	Can change community topic	46	change_communitytopic
183	Can delete community topic	46	delete_communitytopic
184	Can view community topic	46	view_communitytopic
185	Can add community	47	add_community
186	Can change community	47	change_community
187	Can delete community	47	delete_community
188	Can view community	47	view_community
189	Can add community membership	48	add_communitymembership
190	Can change community membership	48	change_communitymembership
191	Can delete community membership	48	delete_communitymembership
192	Can view community membership	48	view_communitymembership
193	Can add email notification settings	49	add_emailnotificationsettings
194	Can change email notification settings	49	change_emailnotificationsettings
195	Can delete email notification settings	49	delete_emailnotificationsettings
196	Can view email notification settings	49	view_emailnotificationsettings
197	Can add community notification subscription	50	add_communitynotificationsubscription
198	Can change community notification subscription	50	change_communitynotificationsubscription
199	Can delete community notification subscription	50	delete_communitynotificationsubscription
200	Can view community notification subscription	50	view_communitynotificationsubscription
201	Can add lesson	51	add_lesson
202	Can change lesson	51	change_lesson
203	Can delete lesson	51	delete_lesson
204	Can view lesson	51	view_lesson
205	Can add course	52	add_course
206	Can change course	52	change_course
207	Can delete course	52	delete_course
208	Can view course	52	view_course
209	Can add course progress	53	add_courseprogress
210	Can change course progress	53	change_courseprogress
211	Can delete course progress	53	delete_courseprogress
212	Can view course progress	53	view_courseprogress
\.


--
-- Data for Name: authtoken_token; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.authtoken_token (key, created, user_id) FROM stdin;
cc7075632a9a30c1f192accf0c6b4e55b923b9ac	2025-11-22 12:09:19.642454+03	1
255b5fb5b3d6b94f910cddb9b5ed9f491a62f2b3	2025-11-24 10:19:24.204289+03	6
\.


--
-- Data for Name: certificates; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.certificates (id, name, description, template_url, criteria) FROM stdin;
\.


--
-- Data for Name: chat_messages; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.chat_messages (id, chat_id, sender_id, content, sent_date, is_edited, edited_date, is_deleted) FROM stdin;
\.


--
-- Data for Name: chat_participants; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.chat_participants (chat_id, user_id, joined_date, left_date, role_in_chat) FROM stdin;
\.


--
-- Data for Name: chats; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.chats (id, name, chat_type, created_by, created_date, is_active) FROM stdin;
\.


--
-- Data for Name: complaints; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.complaints (id, reporter_id, target_type, target_id, reason, description, status, assigned_moderator, created_date, resolved_date) FROM stdin;
\.


--
-- Data for Name: django_admin_log; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.django_admin_log (id, action_time, object_id, object_repr, action_flag, change_message, content_type_id, user_id) FROM stdin;
1	2025-11-11 09:48:33.640139+03	5	GitHub OAuth	3		38	3
2	2025-11-11 09:48:39.46352+03	6	Google OAuth	3		38	3
3	2025-11-17 11:24:39.019554+03	1	Python	1	[{"added": {}}]	10	3
4	2025-11-17 11:24:46.352069+03	2	Django	1	[{"added": {}}]	10	3
5	2025-11-17 11:25:22.69589+03	3	JavaScript	1	[{"added": {}}]	10	3
6	2025-11-17 11:25:28.836848+03	4	HTML	1	[{"added": {}}]	10	3
7	2025-11-17 11:25:36.79559+03	5	CSS	1	[{"added": {}}]	10	3
8	2025-11-17 11:25:49.090143+03	6	Базы данных	1	[{"added": {}}]	10	3
9	2025-11-17 11:25:59.568563+03	7	SQL	1	[{"added": {}}]	10	3
10	2025-11-17 11:26:06.050524+03	8	PostgreSQL	1	[{"added": {}}]	10	3
11	2025-11-17 11:26:15.625208+03	9	Веб-разработка	1	[{"added": {}}]	10	3
12	2025-11-17 11:26:22.299722+03	10	Фронтенд	1	[{"added": {}}]	10	3
13	2025-11-17 11:26:26.197429+03	11	Бэкенд	1	[{"added": {}}]	10	3
14	2025-11-17 11:26:32.474519+03	12	API	1	[{"added": {}}]	10	3
15	2025-11-17 11:26:38.121096+03	13	Аутентификация	1	[{"added": {}}]	10	3
16	2025-11-17 11:26:46.341776+03	14	Безопасность	1	[{"added": {}}]	10	3
17	2025-11-17 11:26:53.118846+03	15	Оптимизация	1	[{"added": {}}]	10	3
18	2025-11-17 11:26:59.058882+03	16	Тестирование	1	[{"added": {}}]	10	3
19	2025-11-17 11:27:08.661492+03	17	Отладка	1	[{"added": {}}]	10	3
20	2025-11-17 11:27:13.271698+03	18	Docker	1	[{"added": {}}]	10	3
21	2025-11-17 11:27:22.227586+03	19	Git	1	[{"added": {}}]	10	3
22	2025-11-17 11:27:27.161045+03	20	Алгоритмы	1	[{"added": {}}]	10	3
\.


--
-- Data for Name: django_content_type; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.django_content_type (id, app_label, model) FROM stdin;
1	admin	logentry
2	auth	permission
3	auth	group
4	contenttypes	contenttype
5	sessions	session
6	GadukaGang	achievement
7	GadukaGang	certificate
8	GadukaGang	chat
9	GadukaGang	section
10	GadukaGang	tag
11	GadukaGang	user
12	GadukaGang	userrank
13	GadukaGang	topic
14	GadukaGang	userprofile
15	GadukaGang	usercertificate
16	GadukaGang	systemlog
17	GadukaGang	post
18	GadukaGang	forumsetting
19	GadukaGang	complaint
20	GadukaGang	chatmessage
21	GadukaGang	topictag
22	GadukaGang	userrankprogress
23	GadukaGang	userachievement
24	GadukaGang	chatparticipant
25	GadukaGang	adminlog
26	GadukaGang	githubauth
27	GadukaGang	moderatoraction
28	GadukaGang	notification
29	GadukaGang	searchindex
30	GadukaGang	postlike
31	GadukaGang	topicrating
32	GadukaGang	topicsubscription
33	GadukaGang	usersubscription
34	sites	site
35	account	emailaddress
36	account	emailconfirmation
37	socialaccount	socialaccount
38	socialaccount	socialapp
39	socialaccount	socialtoken
40	GadukaGang	topicview
41	GadukaGang	practicetopic
42	GadukaGang	userpracticeprogress
43	GadukaGang	practicelevel
44	authtoken	token
45	authtoken	tokenproxy
46	GadukaGang	communitytopic
47	GadukaGang	community
48	GadukaGang	communitymembership
49	GadukaGang	emailnotificationsettings
50	GadukaGang	communitynotificationsubscription
51	GadukaGang	lesson
52	GadukaGang	course
53	GadukaGang	courseprogress
\.


--
-- Data for Name: django_migrations; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.django_migrations (id, app, name, applied) FROM stdin;
1	contenttypes	0001_initial	2025-09-28 15:13:56.500391+03
2	contenttypes	0002_remove_content_type_name	2025-09-28 15:13:56.507934+03
3	auth	0001_initial	2025-09-28 15:13:56.533173+03
4	auth	0002_alter_permission_name_max_length	2025-09-28 15:13:56.536762+03
5	auth	0003_alter_user_email_max_length	2025-09-28 15:13:56.54077+03
6	auth	0004_alter_user_username_opts	2025-09-28 15:13:56.543771+03
7	auth	0005_alter_user_last_login_null	2025-09-28 15:13:56.546772+03
8	auth	0006_require_contenttypes_0002	2025-09-28 15:13:56.547772+03
9	auth	0007_alter_validators_add_error_messages	2025-09-28 15:13:56.549771+03
10	auth	0008_alter_user_username_max_length	2025-09-28 15:13:56.553397+03
11	auth	0009_alter_user_last_name_max_length	2025-09-28 15:13:56.556596+03
12	auth	0010_alter_group_name_max_length	2025-09-28 15:13:56.561385+03
13	auth	0011_update_proxy_permissions	2025-09-28 15:13:56.564538+03
14	auth	0012_alter_user_first_name_max_length	2025-09-28 15:13:56.567718+03
15	GadukaGang	0001_initial	2025-09-28 15:13:56.807089+03
16	GadukaGang	0002_alter_user_options_alter_userachievement_awarded_by_and_more	2025-09-28 15:13:56.838789+03
17	admin	0001_initial	2025-09-28 15:13:56.858593+03
18	admin	0002_logentry_remove_auto_add	2025-09-28 15:13:56.86859+03
19	admin	0003_logentry_add_action_flag_choices	2025-09-28 15:13:56.878592+03
20	sessions	0001_initial	2025-09-28 15:13:56.884949+03
21	GadukaGang	0003_post_dislike_count_post_like_count_and_more	2025-11-09 17:33:20.98795+03
22	account	0001_initial	2025-11-09 18:08:02.630372+03
23	account	0002_email_max_length	2025-11-09 18:08:02.653289+03
24	account	0003_alter_emailaddress_create_unique_verified_email	2025-11-09 18:08:02.683681+03
25	account	0004_alter_emailaddress_drop_unique_email	2025-11-09 18:08:02.715597+03
26	account	0005_emailaddress_idx_upper_email	2025-11-09 18:08:02.735599+03
27	sites	0001_initial	2025-11-09 18:08:02.738597+03
28	sites	0002_alter_domain_unique	2025-11-09 18:08:02.743599+03
29	socialaccount	0001_initial	2025-11-09 18:08:02.820076+03
30	socialaccount	0002_token_max_lengths	2025-11-09 18:08:02.845078+03
31	socialaccount	0003_extra_data_default_dict	2025-11-09 18:08:02.858646+03
32	socialaccount	0004_app_provider_id_settings	2025-11-09 18:08:02.91802+03
33	socialaccount	0005_socialtoken_nullable_app	2025-11-09 18:08:02.939313+03
34	GadukaGang	0004_alter_topictag_tag_alter_topictag_topic	2025-11-13 14:42:33.140774+03
35	GadukaGang	0005_userprofile_karma	2025-11-17 11:10:37.525489+03
36	GadukaGang	0006_topicview	2025-11-17 12:11:45.952563+03
37	GadukaGang	0007_practicetopic_practicelevel_userpracticeprogress	2025-11-17 13:10:40.120165+03
38	GadukaGang	0008_practicelevel_theory_questions	2025-11-20 08:49:25.362334+03
39	GadukaGang	0009_remove_practicelevel_certificate_and_more	2025-11-21 23:49:05.953532+03
40	authtoken	0001_initial	2025-11-21 23:49:06.0999+03
41	authtoken	0002_auto_20160226_1747	2025-11-21 23:49:06.287074+03
42	authtoken	0003_tokenproxy	2025-11-21 23:49:06.298078+03
43	GadukaGang	0010_emailnotificationsettings_community_and_more	2025-11-23 16:15:58.780572+03
44	GadukaGang	0011_community_invite_token_and_notifications	2025-11-23 17:56:15.335431+03
45	GadukaGang	0012_delete_emailnotificationsettings	2025-11-23 18:41:03.702944+03
46	GadukaGang	0013_course_lesson_courseprogress	2025-11-23 21:33:29.06529+03
47	GadukaGang	0014_lesson_test_input_test_output	2025-11-23 22:06:19.219635+03
48	GadukaGang	0015_lesson_test_cases	2025-11-24 00:55:25.01593+03
\.


--
-- Data for Name: django_session; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.django_session (session_key, session_data, expire_date) FROM stdin;
e1zxovobjwyp6x0jg2nsd6ikssehfspc	.eJxVjEEOwiAQRe_C2pAplGF06b5nIANDpWpKUtqV8e7apAvd_vfef6nA21rC1vISJlEXZdXpd4ucHnnegdx5vlWd6rwuU9S7og_a9FAlP6-H-3dQuJVvHQGRTcQkQJKp7xz5zvdAIMbJOYu3DOxHNODRJnAYxx4pRTTJZyL1_gDOtTdL:1vMTeY:-zTDSnnKyl9qTK9hJSP_wuZHQkPJpph3N_F66nik3VU	2025-12-05 19:06:30.855783+03
pvthbz5acrfsvwy13y8be8hdxi1nrawa	.eJxVjDkOwjAUBe_iGlm2AS-U9DlD9DfjALKlOKkQd4dIKaB9M_NeaoR1KePaZR4nVhfl1OF3Q6CH1A3wHeqtaWp1mSfUm6J32vXQWJ7X3f07KNDLt86ShDBFNORMsBCIBGIme_LRGrTomMP5GBgoJxcZJHnPljHYxBSyen8AE205Kg:1v5eFX:dioMGGQZiDxaP53hgjfGJDHaPbX8hkfqBhV3Za9DVKU	2025-10-20 08:59:07.919812+03
ho0rn80e0f6ojodkzso49jxrmnatj0b4	.eJxVjDsOwjAQBe_iGlmY9fpDSc8ZrN21jQMokeKkQtwdIqWA9s3Me6lE69LS2suchqzOyqnD78YkjzJuIN9pvE1apnGZB9abonfa9XXK5XnZ3b-DRr19a2R2x4A-SMYTB6kmQgFxjIaAIgLZCgEiVA9eBCCKtQ6FhdBUS-r9Ad_GN9s:1vNRJl:Deo7RevATmI3bZ_utXgYTmOuHFx0hjpTP9cwriQqot0	2025-12-08 10:49:01.842807+03
hfx3c0by61pna39sejeygzemd3c176w1	.eJxVjEEOwiAQRe_C2pAplGF06b5nIANDpWpKUtqV8e7apAvd_vfef6nA21rC1vISJlEXZdXpd4ucHnnegdx5vlWd6rwuU9S7og_a9FAlP6-H-3dQuJVvHQGRTcQkQJKp7xz5zvdAIMbJOYu3DOxHNODRJnAYxx4pRTTJZyL1_gDOtTdL:1vIiAl:U-XBu_RGNICMoL0uhWqsvrMqRScZhAsn51xcRgz3Dn8	2025-11-25 09:48:11.358604+03
ktnw0klvg5eamgr7d1sbv67xz2ssf4a5	.eJxVjEEOwiAQRe_C2pAplGF06b5nIANDpWpKUtqV8e7apAvd_vfef6nA21rC1vISJlEXZdXpd4ucHnnegdx5vlWd6rwuU9S7og_a9FAlP6-H-3dQuJVvHQGRTcQkQJKp7xz5zvdAIMbJOYu3DOxHNODRJnAYxx4pRTTJZyL1_gDOtTdL:1vIiIl:6TLEhQjyCUDbaSb19S06nNXmy-LWgumy2HkXwARGUgQ	2025-11-25 09:56:27.894918+03
n1dfd14btuv4q2t72wk58nylzu2lix3q	.eJxVj7FuwyAQhl8FsXiprDPGQD02c5-gjawDLrWTGiKMp6rvHmN5SJZvuP-_T3d_fMA1j8O6UBomz3ve8rfnmUV3o1ACf8XwE2sXQ06TrUulPtKl_oyefj-O7otgxGXcti0ohcIq58F4MrLpjG60BANedP6dvG4RUF-UAK1aB52yF6mMs0o4TcZs0mm-x5QHSimmhfdf_HsFKZpCKXZCYUs7cScw0bPqFOcZg69YtFdymW03sRAZ5vLJmolVhzthuFX8_P8ATWZaMw:1vMqfK:wE1A75LvZvOKdY2tLCQ0uMgqW-O952sFW6x6R_5WyzQ	2025-12-06 19:40:50.450355+03
36bofq1e90nzzo2bm24pdkj6nmy55vc5	.eJxVjEEOwiAQRe_C2pAppQPt0r1nIMBMLWrAlDbRGO-uTbrp9r_3_ke4yrWmkh2_nml-i6FR0CPASTi_LpNbK88ukRhEKw5b8PHOeQN08_laZCx5mVOQmyJ3WuWlED_Ou3s4mHyd_nUARK8CRgJLbHXTWdMYDRZIddQzmdaDNyMqMNhG6DCMGm0MqKJha8X3B_WNP7o:1vIjbP:_dlF4Sa6lljDIdWS0UEUjGf0L3TpY2HX8E_QvVgna7s	2025-11-25 11:19:47.175299+03
6wab5nzh2hvgictnu681jhmjskr4d5pa	.eJxVjEEOwiAQRe_C2pAplGF06b5nIANDpWpKUtqV8e7apAvd_vfef6nA21rC1vISJlEXZdXpd4ucHnnegdx5vlWd6rwuU9S7og_a9FAlP6-H-3dQuJVvHQGRTcQkQJKp7xz5zvdAIMbJOYu3DOxHNODRJnAYxx4pRTTJZyL1_gDOtTdL:1vKvJi:Ie2k0bb1FhchZZihVWHkTVUm-4DSTN5cJVNqk2dqdXY	2025-12-01 12:14:34.532241+03
73p6kwxktn4lit4pfnv7lpqahat3pep9	.eJxVjEEOwjAMBP-SM6oc16UuN_hI5DhBiahSiSYnxN9pUQ9w3NndeRknrSbX1vh0OZiLIXP6ZV70EcteyDzvuBPVpZXafTdHvXbXLcVSs0rNS7kdrz9VkjVtHrD9GSx6lj7QqOzp7lEAeApoiVh4Ap1G4IiKHOLAjAQWekANAQbz_gCQYTsN:1vNIrT:sTbd61C8kxKZNG1ZGUzL13Ttvxabh_HGvLPX8oYxQwc	2025-12-08 01:47:15.204618+03
8mm9ek1r0gr01ttcgd975uf0htysusaf	.eJxVjEEOwjAMBP-SM6oc16UuN_hI5DhBiahSiSYnxN9pUQ9w3NndeRknrSbX1vh0OZiLIXP6ZV70EcteyDzvuBPVpZXafTdHvXbXLcVSs0rNS7kdrz9VkjVtHrD9GSx6lj7QqOzp7lEAeApoiVh4Ap1G4IiKHOLAjAQWekANAQbz_gCQYTsN:1vNIrV:GkCN--0dYIZc2sbchHqKpnSHCDXjjc8yQuB25R3kp-A	2025-12-08 01:47:17.657117+03
ll3gvuqdrdqx5v8hweuwfmdvmongpa70	.eJxVjEEOwiAQRe_C2pAplGF06b5nIANDpWpKUtqV8e7apAvd_vfef6nA21rC1vISJlEXZdXpd4ucHnnegdx5vlWd6rwuU9S7og_a9FAlP6-H-3dQuJVvHQGRTcQkQJKp7xz5zvdAIMbJOYu3DOxHNODRJnAYxx4pRTTJZyL1_gDOtTdL:1vLxYy:19iYLPl9EHqgpX8_AG72-z3VtZQl9m7uQvFO6brKu88	2025-12-04 08:50:36.352975+03
\.


--
-- Data for Name: django_site; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.django_site (id, domain, name) FROM stdin;
1	localhost:9876	localhost:9876
\.


--
-- Data for Name: forum_settings; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.forum_settings (id, setting_name, setting_value, category, last_modified, modified_by) FROM stdin;
1	forum_name	"Gaduka Gang"	general	2025-09-27 16:56:36.715307	\N
2	posts_per_page	20	display	2025-09-27 16:56:36.715307	\N
3	topics_per_page	30	display	2025-09-27 16:56:36.715307	\N
4	max_signature_length	200	user	2025-09-27 16:56:36.715307	\N
5	allow_user_registration	true	security	2025-09-27 16:56:36.715307	\N
\.


--
-- Data for Name: posts; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.posts (id, topic_id, author_id, content, created_date, last_edited_date, edit_count, is_deleted) FROM stdin;
\.


--
-- Data for Name: sections; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.sections (id, name, description, created_by, created_date) FROM stdin;
1	Общие вопросы Python	Общие вопросы и обсуждения о языке Python	\N	2025-09-27 16:56:14.732605
2	Проблемы и ошибки	Обсуждение ошибок и проблем в коде	\N	2025-09-27 16:56:14.732605
3	Библиотеки и фреймворки	Обсуждение популярных библиотек и фреймворков	\N	2025-09-27 16:56:14.732605
4	Искусственный интеллект и машинное обучение	Обсуждение AI и ML технологий	\N	2025-09-27 16:56:14.732605
5	Веб-разработка	Вопросы веб-разработки на Python	\N	2025-09-27 16:56:14.732605
6	Автоматизация и скрипты	Создание скриптов и автоматизация задач	\N	2025-09-27 16:56:14.732605
\.


--
-- Data for Name: socialaccount_socialaccount; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.socialaccount_socialaccount (id, provider, uid, last_login, date_joined, extra_data, user_id) FROM stdin;
\.


--
-- Data for Name: socialaccount_socialapp; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.socialaccount_socialapp (id, provider, name, client_id, secret, key, provider_id, settings) FROM stdin;
\.


--
-- Data for Name: socialaccount_socialapp_sites; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.socialaccount_socialapp_sites (id, socialapp_id, site_id) FROM stdin;
\.


--
-- Data for Name: socialaccount_socialtoken; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.socialaccount_socialtoken (id, token, token_secret, expires_at, account_id, app_id) FROM stdin;
\.


--
-- Data for Name: system_logs; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.system_logs (id, user_id, action_type, action_level, description, affected_resource_type, affected_resource_id, "timestamp") FROM stdin;
\.


--
-- Data for Name: tags; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.tags (id, name, color) FROM stdin;
1	python	#3572A5
2	django	#092E20
3	flask	#E3242B
4	fastapi	#009688
5	async	#FFD43B
6	oop	#6A5ACD
7	database	#4EA94B
8	ai	#FF6B6B
9	ml	#4ECDC4
\.


--
-- Data for Name: topic_tags; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.topic_tags (topic_id, tag_id) FROM stdin;
\.


--
-- Data for Name: topics; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.topics (id, section_id, title, author_id, created_date, last_post_date, is_pinned, view_count) FROM stdin;
\.


--
-- Data for Name: user_achievements; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.user_achievements (user_id, achievement_id, earned_date, awarded_by) FROM stdin;
\.


--
-- Data for Name: user_certificates; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.user_certificates (id, user_id, certificate_id, awarded_date, awarded_by, expiration_date) FROM stdin;
\.


--
-- Data for Name: user_profiles; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.user_profiles (user_id, avatar_url, bio, signature, post_count, join_date, last_activity) FROM stdin;
\.


--
-- Data for Name: user_rank_progress; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.user_rank_progress (user_id, rank_id, current_points, progress_percentage) FROM stdin;
\.


--
-- Data for Name: user_ranks; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.user_ranks (id, name, required_points, icon_url) FROM stdin;
1	Новичок	0	/static/images/ranks/beginner.png
2	Участник	50	/static/images/ranks/member.png
3	Эксперт	200	/static/images/ranks/expert.png
4	Мастер	500	/static/images/ranks/master.png
5	Гуру	1000	/static/images/ranks/guru.png
\.


--
-- Data for Name: users; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.users (id, username, email, password_hash, registration_date, last_login, is_active, role) FROM stdin;
\.


--
-- Name: GadukaGang_achievement_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public."GadukaGang_achievement_id_seq"', 2, true);


--
-- Name: GadukaGang_adminlog_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public."GadukaGang_adminlog_id_seq"', 1, false);


--
-- Name: GadukaGang_certificate_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public."GadukaGang_certificate_id_seq"', 32, true);


--
-- Name: GadukaGang_chat_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public."GadukaGang_chat_id_seq"', 1, false);


--
-- Name: GadukaGang_chatmessage_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public."GadukaGang_chatmessage_id_seq"', 1, false);


--
-- Name: GadukaGang_chatparticipant_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public."GadukaGang_chatparticipant_id_seq"', 1, false);


--
-- Name: GadukaGang_community_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public."GadukaGang_community_id_seq"', 2, true);


--
-- Name: GadukaGang_communitymembership_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public."GadukaGang_communitymembership_id_seq"', 22, true);


--
-- Name: GadukaGang_communitynotificationsubscription_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public."GadukaGang_communitynotificationsubscription_id_seq"', 1, false);


--
-- Name: GadukaGang_communitytopic_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public."GadukaGang_communitytopic_id_seq"', 11, true);


--
-- Name: GadukaGang_complaint_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public."GadukaGang_complaint_id_seq"', 1, false);


--
-- Name: GadukaGang_course_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public."GadukaGang_course_id_seq"', 3, true);


--
-- Name: GadukaGang_courseprogress_completed_lessons_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public."GadukaGang_courseprogress_completed_lessons_id_seq"', 15, true);


--
-- Name: GadukaGang_courseprogress_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public."GadukaGang_courseprogress_id_seq"', 4, true);


--
-- Name: GadukaGang_forumsetting_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public."GadukaGang_forumsetting_id_seq"', 1, false);


--
-- Name: GadukaGang_githubauth_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public."GadukaGang_githubauth_id_seq"', 1, false);


--
-- Name: GadukaGang_lesson_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public."GadukaGang_lesson_id_seq"', 31, true);


--
-- Name: GadukaGang_moderatoraction_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public."GadukaGang_moderatoraction_id_seq"', 1, false);


--
-- Name: GadukaGang_notification_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public."GadukaGang_notification_id_seq"', 1, false);


--
-- Name: GadukaGang_post_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public."GadukaGang_post_id_seq"', 19, true);


--
-- Name: GadukaGang_postlike_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public."GadukaGang_postlike_id_seq"', 21, true);


--
-- Name: GadukaGang_searchindex_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public."GadukaGang_searchindex_id_seq"', 1, false);


--
-- Name: GadukaGang_section_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public."GadukaGang_section_id_seq"', 6, true);


--
-- Name: GadukaGang_systemlog_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public."GadukaGang_systemlog_id_seq"', 9, true);


--
-- Name: GadukaGang_tag_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public."GadukaGang_tag_id_seq"', 21, true);


--
-- Name: GadukaGang_topic_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public."GadukaGang_topic_id_seq"', 18, true);


--
-- Name: GadukaGang_topicrating_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public."GadukaGang_topicrating_id_seq"', 4, true);


--
-- Name: GadukaGang_topicsubscription_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public."GadukaGang_topicsubscription_id_seq"', 1, false);


--
-- Name: GadukaGang_topictag_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public."GadukaGang_topictag_id_seq"', 17, true);


--
-- Name: GadukaGang_topicview_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public."GadukaGang_topicview_id_seq"', 21, true);


--
-- Name: GadukaGang_user_groups_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public."GadukaGang_user_groups_id_seq"', 1, false);


--
-- Name: GadukaGang_user_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public."GadukaGang_user_id_seq"', 6, true);


--
-- Name: GadukaGang_user_user_permissions_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public."GadukaGang_user_user_permissions_id_seq"', 1, false);


--
-- Name: GadukaGang_userachievement_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public."GadukaGang_userachievement_id_seq"', 3, true);


--
-- Name: GadukaGang_usercertificate_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public."GadukaGang_usercertificate_id_seq"', 1, true);


--
-- Name: GadukaGang_userrank_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public."GadukaGang_userrank_id_seq"', 1, true);


--
-- Name: GadukaGang_usersubscription_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public."GadukaGang_usersubscription_id_seq"', 1, false);


--
-- Name: account_emailaddress_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.account_emailaddress_id_seq', 1, true);


--
-- Name: account_emailconfirmation_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.account_emailconfirmation_id_seq', 1, false);


--
-- Name: achievements_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.achievements_id_seq', 4, true);


--
-- Name: auth_group_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.auth_group_id_seq', 1, false);


--
-- Name: auth_group_permissions_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.auth_group_permissions_id_seq', 1, false);


--
-- Name: auth_permission_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.auth_permission_id_seq', 212, true);


--
-- Name: certificates_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.certificates_id_seq', 1, false);


--
-- Name: chat_messages_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.chat_messages_id_seq', 1, false);


--
-- Name: chats_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.chats_id_seq', 1, false);


--
-- Name: complaints_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.complaints_id_seq', 1, false);


--
-- Name: django_admin_log_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.django_admin_log_id_seq', 22, true);


--
-- Name: django_content_type_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.django_content_type_id_seq', 53, true);


--
-- Name: django_migrations_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.django_migrations_id_seq', 48, true);


--
-- Name: django_site_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.django_site_id_seq', 1, true);


--
-- Name: forum_settings_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.forum_settings_id_seq', 5, true);


--
-- Name: posts_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.posts_id_seq', 1, false);


--
-- Name: sections_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.sections_id_seq', 6, true);


--
-- Name: socialaccount_socialaccount_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.socialaccount_socialaccount_id_seq', 1, false);


--
-- Name: socialaccount_socialapp_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.socialaccount_socialapp_id_seq', 6, true);


--
-- Name: socialaccount_socialapp_sites_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.socialaccount_socialapp_sites_id_seq', 6, true);


--
-- Name: socialaccount_socialtoken_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.socialaccount_socialtoken_id_seq', 1, false);


--
-- Name: system_logs_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.system_logs_id_seq', 1, false);


--
-- Name: tags_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.tags_id_seq', 9, true);


--
-- Name: topics_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.topics_id_seq', 1, false);


--
-- Name: user_certificates_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.user_certificates_id_seq', 1, false);


--
-- Name: user_ranks_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.user_ranks_id_seq', 5, true);


--
-- Name: users_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.users_id_seq', 1, false);


--
-- Name: GadukaGang_achievement GadukaGang_achievement_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public."GadukaGang_achievement"
    ADD CONSTRAINT "GadukaGang_achievement_pkey" PRIMARY KEY (id);


--
-- Name: GadukaGang_adminlog GadukaGang_adminlog_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public."GadukaGang_adminlog"
    ADD CONSTRAINT "GadukaGang_adminlog_pkey" PRIMARY KEY (id);


--
-- Name: GadukaGang_certificate GadukaGang_certificate_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public."GadukaGang_certificate"
    ADD CONSTRAINT "GadukaGang_certificate_pkey" PRIMARY KEY (id);


--
-- Name: GadukaGang_chat GadukaGang_chat_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public."GadukaGang_chat"
    ADD CONSTRAINT "GadukaGang_chat_pkey" PRIMARY KEY (id);


--
-- Name: GadukaGang_chatmessage GadukaGang_chatmessage_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public."GadukaGang_chatmessage"
    ADD CONSTRAINT "GadukaGang_chatmessage_pkey" PRIMARY KEY (id);


--
-- Name: GadukaGang_chatparticipant GadukaGang_chatparticipant_chat_id_user_id_a38b375e_uniq; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public."GadukaGang_chatparticipant"
    ADD CONSTRAINT "GadukaGang_chatparticipant_chat_id_user_id_a38b375e_uniq" UNIQUE (chat_id, user_id);


--
-- Name: GadukaGang_chatparticipant GadukaGang_chatparticipant_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public."GadukaGang_chatparticipant"
    ADD CONSTRAINT "GadukaGang_chatparticipant_pkey" PRIMARY KEY (id);


--
-- Name: GadukaGang_community GadukaGang_community_invite_token_fd9613cd_uniq; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public."GadukaGang_community"
    ADD CONSTRAINT "GadukaGang_community_invite_token_fd9613cd_uniq" UNIQUE (invite_token);


--
-- Name: GadukaGang_community GadukaGang_community_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public."GadukaGang_community"
    ADD CONSTRAINT "GadukaGang_community_pkey" PRIMARY KEY (id);


--
-- Name: GadukaGang_communitymembership GadukaGang_communitymemb_community_id_user_id_56989a5e_uniq; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public."GadukaGang_communitymembership"
    ADD CONSTRAINT "GadukaGang_communitymemb_community_id_user_id_56989a5e_uniq" UNIQUE (community_id, user_id);


--
-- Name: GadukaGang_communitymembership GadukaGang_communitymembership_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public."GadukaGang_communitymembership"
    ADD CONSTRAINT "GadukaGang_communitymembership_pkey" PRIMARY KEY (id);


--
-- Name: GadukaGang_communitynotificationsubscription GadukaGang_communitynoti_community_id_user_id_bb5529ba_uniq; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public."GadukaGang_communitynotificationsubscription"
    ADD CONSTRAINT "GadukaGang_communitynoti_community_id_user_id_bb5529ba_uniq" UNIQUE (community_id, user_id);


--
-- Name: GadukaGang_communitynotificationsubscription GadukaGang_communitynotificationsubscription_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public."GadukaGang_communitynotificationsubscription"
    ADD CONSTRAINT "GadukaGang_communitynotificationsubscription_pkey" PRIMARY KEY (id);


--
-- Name: GadukaGang_communitytopic GadukaGang_communitytopic_community_id_topic_id_177241f9_uniq; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public."GadukaGang_communitytopic"
    ADD CONSTRAINT "GadukaGang_communitytopic_community_id_topic_id_177241f9_uniq" UNIQUE (community_id, topic_id);


--
-- Name: GadukaGang_communitytopic GadukaGang_communitytopic_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public."GadukaGang_communitytopic"
    ADD CONSTRAINT "GadukaGang_communitytopic_pkey" PRIMARY KEY (id);


--
-- Name: GadukaGang_complaint GadukaGang_complaint_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public."GadukaGang_complaint"
    ADD CONSTRAINT "GadukaGang_complaint_pkey" PRIMARY KEY (id);


--
-- Name: GadukaGang_course GadukaGang_course_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public."GadukaGang_course"
    ADD CONSTRAINT "GadukaGang_course_pkey" PRIMARY KEY (id);


--
-- Name: GadukaGang_courseprogress_completed_lessons GadukaGang_courseprogres_courseprogress_id_lesson_1b1e990e_uniq; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public."GadukaGang_courseprogress_completed_lessons"
    ADD CONSTRAINT "GadukaGang_courseprogres_courseprogress_id_lesson_1b1e990e_uniq" UNIQUE (courseprogress_id, lesson_id);


--
-- Name: GadukaGang_courseprogress_completed_lessons GadukaGang_courseprogress_completed_lessons_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public."GadukaGang_courseprogress_completed_lessons"
    ADD CONSTRAINT "GadukaGang_courseprogress_completed_lessons_pkey" PRIMARY KEY (id);


--
-- Name: GadukaGang_courseprogress GadukaGang_courseprogress_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public."GadukaGang_courseprogress"
    ADD CONSTRAINT "GadukaGang_courseprogress_pkey" PRIMARY KEY (id);


--
-- Name: GadukaGang_courseprogress GadukaGang_courseprogress_user_id_course_id_4af9d87f_uniq; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public."GadukaGang_courseprogress"
    ADD CONSTRAINT "GadukaGang_courseprogress_user_id_course_id_4af9d87f_uniq" UNIQUE (user_id, course_id);


--
-- Name: GadukaGang_forumsetting GadukaGang_forumsetting_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public."GadukaGang_forumsetting"
    ADD CONSTRAINT "GadukaGang_forumsetting_pkey" PRIMARY KEY (id);


--
-- Name: GadukaGang_forumsetting GadukaGang_forumsetting_setting_name_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public."GadukaGang_forumsetting"
    ADD CONSTRAINT "GadukaGang_forumsetting_setting_name_key" UNIQUE (setting_name);


--
-- Name: GadukaGang_githubauth GadukaGang_githubauth_github_id_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public."GadukaGang_githubauth"
    ADD CONSTRAINT "GadukaGang_githubauth_github_id_key" UNIQUE (github_id);


--
-- Name: GadukaGang_githubauth GadukaGang_githubauth_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public."GadukaGang_githubauth"
    ADD CONSTRAINT "GadukaGang_githubauth_pkey" PRIMARY KEY (id);


--
-- Name: GadukaGang_githubauth GadukaGang_githubauth_user_id_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public."GadukaGang_githubauth"
    ADD CONSTRAINT "GadukaGang_githubauth_user_id_key" UNIQUE (user_id);


--
-- Name: GadukaGang_lesson GadukaGang_lesson_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public."GadukaGang_lesson"
    ADD CONSTRAINT "GadukaGang_lesson_pkey" PRIMARY KEY (id);


--
-- Name: GadukaGang_moderatoraction GadukaGang_moderatoraction_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public."GadukaGang_moderatoraction"
    ADD CONSTRAINT "GadukaGang_moderatoraction_pkey" PRIMARY KEY (id);


--
-- Name: GadukaGang_notification GadukaGang_notification_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public."GadukaGang_notification"
    ADD CONSTRAINT "GadukaGang_notification_pkey" PRIMARY KEY (id);


--
-- Name: GadukaGang_post GadukaGang_post_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public."GadukaGang_post"
    ADD CONSTRAINT "GadukaGang_post_pkey" PRIMARY KEY (id);


--
-- Name: GadukaGang_postlike GadukaGang_postlike_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public."GadukaGang_postlike"
    ADD CONSTRAINT "GadukaGang_postlike_pkey" PRIMARY KEY (id);


--
-- Name: GadukaGang_postlike GadukaGang_postlike_post_id_user_id_f890844a_uniq; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public."GadukaGang_postlike"
    ADD CONSTRAINT "GadukaGang_postlike_post_id_user_id_f890844a_uniq" UNIQUE (post_id, user_id);


--
-- Name: GadukaGang_searchindex GadukaGang_searchindex_content_type_object_id_831ed45c_uniq; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public."GadukaGang_searchindex"
    ADD CONSTRAINT "GadukaGang_searchindex_content_type_object_id_831ed45c_uniq" UNIQUE (content_type, object_id);


--
-- Name: GadukaGang_searchindex GadukaGang_searchindex_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public."GadukaGang_searchindex"
    ADD CONSTRAINT "GadukaGang_searchindex_pkey" PRIMARY KEY (id);


--
-- Name: GadukaGang_section GadukaGang_section_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public."GadukaGang_section"
    ADD CONSTRAINT "GadukaGang_section_pkey" PRIMARY KEY (id);


--
-- Name: GadukaGang_systemlog GadukaGang_systemlog_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public."GadukaGang_systemlog"
    ADD CONSTRAINT "GadukaGang_systemlog_pkey" PRIMARY KEY (id);


--
-- Name: GadukaGang_tag GadukaGang_tag_name_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public."GadukaGang_tag"
    ADD CONSTRAINT "GadukaGang_tag_name_key" UNIQUE (name);


--
-- Name: GadukaGang_tag GadukaGang_tag_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public."GadukaGang_tag"
    ADD CONSTRAINT "GadukaGang_tag_pkey" PRIMARY KEY (id);


--
-- Name: GadukaGang_topic GadukaGang_topic_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public."GadukaGang_topic"
    ADD CONSTRAINT "GadukaGang_topic_pkey" PRIMARY KEY (id);


--
-- Name: GadukaGang_topicrating GadukaGang_topicrating_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public."GadukaGang_topicrating"
    ADD CONSTRAINT "GadukaGang_topicrating_pkey" PRIMARY KEY (id);


--
-- Name: GadukaGang_topicrating GadukaGang_topicrating_topic_id_user_id_1641733b_uniq; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public."GadukaGang_topicrating"
    ADD CONSTRAINT "GadukaGang_topicrating_topic_id_user_id_1641733b_uniq" UNIQUE (topic_id, user_id);


--
-- Name: GadukaGang_topicsubscription GadukaGang_topicsubscription_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public."GadukaGang_topicsubscription"
    ADD CONSTRAINT "GadukaGang_topicsubscription_pkey" PRIMARY KEY (id);


--
-- Name: GadukaGang_topicsubscription GadukaGang_topicsubscription_topic_id_user_id_e4fa19d9_uniq; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public."GadukaGang_topicsubscription"
    ADD CONSTRAINT "GadukaGang_topicsubscription_topic_id_user_id_e4fa19d9_uniq" UNIQUE (topic_id, user_id);


--
-- Name: GadukaGang_topictag GadukaGang_topictag_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public."GadukaGang_topictag"
    ADD CONSTRAINT "GadukaGang_topictag_pkey" PRIMARY KEY (id);


--
-- Name: GadukaGang_topictag GadukaGang_topictag_topic_id_tag_id_27a8dcd9_uniq; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public."GadukaGang_topictag"
    ADD CONSTRAINT "GadukaGang_topictag_topic_id_tag_id_27a8dcd9_uniq" UNIQUE (topic_id, tag_id);


--
-- Name: GadukaGang_topicview GadukaGang_topicview_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public."GadukaGang_topicview"
    ADD CONSTRAINT "GadukaGang_topicview_pkey" PRIMARY KEY (id);


--
-- Name: GadukaGang_topicview GadukaGang_topicview_topic_id_user_id_5e5cee75_uniq; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public."GadukaGang_topicview"
    ADD CONSTRAINT "GadukaGang_topicview_topic_id_user_id_5e5cee75_uniq" UNIQUE (topic_id, user_id);


--
-- Name: GadukaGang_user_groups GadukaGang_user_groups_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public."GadukaGang_user_groups"
    ADD CONSTRAINT "GadukaGang_user_groups_pkey" PRIMARY KEY (id);


--
-- Name: GadukaGang_user_groups GadukaGang_user_groups_user_id_group_id_e2960f9f_uniq; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public."GadukaGang_user_groups"
    ADD CONSTRAINT "GadukaGang_user_groups_user_id_group_id_e2960f9f_uniq" UNIQUE (user_id, group_id);


--
-- Name: GadukaGang_user GadukaGang_user_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public."GadukaGang_user"
    ADD CONSTRAINT "GadukaGang_user_pkey" PRIMARY KEY (id);


--
-- Name: GadukaGang_user_user_permissions GadukaGang_user_user_per_user_id_permission_id_76c457f5_uniq; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public."GadukaGang_user_user_permissions"
    ADD CONSTRAINT "GadukaGang_user_user_per_user_id_permission_id_76c457f5_uniq" UNIQUE (user_id, permission_id);


--
-- Name: GadukaGang_user_user_permissions GadukaGang_user_user_permissions_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public."GadukaGang_user_user_permissions"
    ADD CONSTRAINT "GadukaGang_user_user_permissions_pkey" PRIMARY KEY (id);


--
-- Name: GadukaGang_user GadukaGang_user_username_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public."GadukaGang_user"
    ADD CONSTRAINT "GadukaGang_user_username_key" UNIQUE (username);


--
-- Name: GadukaGang_userachievement GadukaGang_userachievement_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public."GadukaGang_userachievement"
    ADD CONSTRAINT "GadukaGang_userachievement_pkey" PRIMARY KEY (id);


--
-- Name: GadukaGang_userachievement GadukaGang_userachievement_user_id_achievement_id_4d7ae7bb_uniq; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public."GadukaGang_userachievement"
    ADD CONSTRAINT "GadukaGang_userachievement_user_id_achievement_id_4d7ae7bb_uniq" UNIQUE (user_id, achievement_id);


--
-- Name: GadukaGang_usercertificate GadukaGang_usercertificate_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public."GadukaGang_usercertificate"
    ADD CONSTRAINT "GadukaGang_usercertificate_pkey" PRIMARY KEY (id);


--
-- Name: GadukaGang_userprofile GadukaGang_userprofile_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public."GadukaGang_userprofile"
    ADD CONSTRAINT "GadukaGang_userprofile_pkey" PRIMARY KEY (user_id);


--
-- Name: GadukaGang_userrank GadukaGang_userrank_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public."GadukaGang_userrank"
    ADD CONSTRAINT "GadukaGang_userrank_pkey" PRIMARY KEY (id);


--
-- Name: GadukaGang_userrankprogress GadukaGang_userrankprogress_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public."GadukaGang_userrankprogress"
    ADD CONSTRAINT "GadukaGang_userrankprogress_pkey" PRIMARY KEY (user_id);


--
-- Name: GadukaGang_usersubscription GadukaGang_usersubscript_subscriber_id_subscribed_98c55131_uniq; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public."GadukaGang_usersubscription"
    ADD CONSTRAINT "GadukaGang_usersubscript_subscriber_id_subscribed_98c55131_uniq" UNIQUE (subscriber_id, subscribed_to_id);


--
-- Name: GadukaGang_usersubscription GadukaGang_usersubscription_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public."GadukaGang_usersubscription"
    ADD CONSTRAINT "GadukaGang_usersubscription_pkey" PRIMARY KEY (id);


--
-- Name: account_emailaddress account_emailaddress_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.account_emailaddress
    ADD CONSTRAINT account_emailaddress_pkey PRIMARY KEY (id);


--
-- Name: account_emailaddress account_emailaddress_user_id_email_987c8728_uniq; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.account_emailaddress
    ADD CONSTRAINT account_emailaddress_user_id_email_987c8728_uniq UNIQUE (user_id, email);


--
-- Name: account_emailconfirmation account_emailconfirmation_key_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.account_emailconfirmation
    ADD CONSTRAINT account_emailconfirmation_key_key UNIQUE (key);


--
-- Name: account_emailconfirmation account_emailconfirmation_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.account_emailconfirmation
    ADD CONSTRAINT account_emailconfirmation_pkey PRIMARY KEY (id);


--
-- Name: achievements achievements_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.achievements
    ADD CONSTRAINT achievements_pkey PRIMARY KEY (id);


--
-- Name: auth_group auth_group_name_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.auth_group
    ADD CONSTRAINT auth_group_name_key UNIQUE (name);


--
-- Name: auth_group_permissions auth_group_permissions_group_id_permission_id_0cd325b0_uniq; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.auth_group_permissions
    ADD CONSTRAINT auth_group_permissions_group_id_permission_id_0cd325b0_uniq UNIQUE (group_id, permission_id);


--
-- Name: auth_group_permissions auth_group_permissions_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.auth_group_permissions
    ADD CONSTRAINT auth_group_permissions_pkey PRIMARY KEY (id);


--
-- Name: auth_group auth_group_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.auth_group
    ADD CONSTRAINT auth_group_pkey PRIMARY KEY (id);


--
-- Name: auth_permission auth_permission_content_type_id_codename_01ab375a_uniq; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.auth_permission
    ADD CONSTRAINT auth_permission_content_type_id_codename_01ab375a_uniq UNIQUE (content_type_id, codename);


--
-- Name: auth_permission auth_permission_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.auth_permission
    ADD CONSTRAINT auth_permission_pkey PRIMARY KEY (id);


--
-- Name: authtoken_token authtoken_token_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.authtoken_token
    ADD CONSTRAINT authtoken_token_pkey PRIMARY KEY (key);


--
-- Name: authtoken_token authtoken_token_user_id_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.authtoken_token
    ADD CONSTRAINT authtoken_token_user_id_key UNIQUE (user_id);


--
-- Name: certificates certificates_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.certificates
    ADD CONSTRAINT certificates_pkey PRIMARY KEY (id);


--
-- Name: chat_messages chat_messages_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.chat_messages
    ADD CONSTRAINT chat_messages_pkey PRIMARY KEY (id);


--
-- Name: chat_participants chat_participants_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.chat_participants
    ADD CONSTRAINT chat_participants_pkey PRIMARY KEY (chat_id, user_id);


--
-- Name: chats chats_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.chats
    ADD CONSTRAINT chats_pkey PRIMARY KEY (id);


--
-- Name: complaints complaints_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.complaints
    ADD CONSTRAINT complaints_pkey PRIMARY KEY (id);


--
-- Name: django_admin_log django_admin_log_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.django_admin_log
    ADD CONSTRAINT django_admin_log_pkey PRIMARY KEY (id);


--
-- Name: django_content_type django_content_type_app_label_model_76bd3d3b_uniq; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.django_content_type
    ADD CONSTRAINT django_content_type_app_label_model_76bd3d3b_uniq UNIQUE (app_label, model);


--
-- Name: django_content_type django_content_type_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.django_content_type
    ADD CONSTRAINT django_content_type_pkey PRIMARY KEY (id);


--
-- Name: django_migrations django_migrations_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.django_migrations
    ADD CONSTRAINT django_migrations_pkey PRIMARY KEY (id);


--
-- Name: django_session django_session_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.django_session
    ADD CONSTRAINT django_session_pkey PRIMARY KEY (session_key);


--
-- Name: django_site django_site_domain_a2e37b91_uniq; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.django_site
    ADD CONSTRAINT django_site_domain_a2e37b91_uniq UNIQUE (domain);


--
-- Name: django_site django_site_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.django_site
    ADD CONSTRAINT django_site_pkey PRIMARY KEY (id);


--
-- Name: forum_settings forum_settings_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.forum_settings
    ADD CONSTRAINT forum_settings_pkey PRIMARY KEY (id);


--
-- Name: forum_settings forum_settings_setting_name_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.forum_settings
    ADD CONSTRAINT forum_settings_setting_name_key UNIQUE (setting_name);


--
-- Name: posts posts_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.posts
    ADD CONSTRAINT posts_pkey PRIMARY KEY (id);


--
-- Name: sections sections_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.sections
    ADD CONSTRAINT sections_pkey PRIMARY KEY (id);


--
-- Name: socialaccount_socialaccount socialaccount_socialaccount_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.socialaccount_socialaccount
    ADD CONSTRAINT socialaccount_socialaccount_pkey PRIMARY KEY (id);


--
-- Name: socialaccount_socialaccount socialaccount_socialaccount_provider_uid_fc810c6e_uniq; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.socialaccount_socialaccount
    ADD CONSTRAINT socialaccount_socialaccount_provider_uid_fc810c6e_uniq UNIQUE (provider, uid);


--
-- Name: socialaccount_socialapp_sites socialaccount_socialapp__socialapp_id_site_id_71a9a768_uniq; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.socialaccount_socialapp_sites
    ADD CONSTRAINT socialaccount_socialapp__socialapp_id_site_id_71a9a768_uniq UNIQUE (socialapp_id, site_id);


--
-- Name: socialaccount_socialapp socialaccount_socialapp_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.socialaccount_socialapp
    ADD CONSTRAINT socialaccount_socialapp_pkey PRIMARY KEY (id);


--
-- Name: socialaccount_socialapp_sites socialaccount_socialapp_sites_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.socialaccount_socialapp_sites
    ADD CONSTRAINT socialaccount_socialapp_sites_pkey PRIMARY KEY (id);


--
-- Name: socialaccount_socialtoken socialaccount_socialtoken_app_id_account_id_fca4e0ac_uniq; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.socialaccount_socialtoken
    ADD CONSTRAINT socialaccount_socialtoken_app_id_account_id_fca4e0ac_uniq UNIQUE (app_id, account_id);


--
-- Name: socialaccount_socialtoken socialaccount_socialtoken_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.socialaccount_socialtoken
    ADD CONSTRAINT socialaccount_socialtoken_pkey PRIMARY KEY (id);


--
-- Name: system_logs system_logs_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.system_logs
    ADD CONSTRAINT system_logs_pkey PRIMARY KEY (id);


--
-- Name: tags tags_name_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.tags
    ADD CONSTRAINT tags_name_key UNIQUE (name);


--
-- Name: tags tags_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.tags
    ADD CONSTRAINT tags_pkey PRIMARY KEY (id);


--
-- Name: topic_tags topic_tags_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.topic_tags
    ADD CONSTRAINT topic_tags_pkey PRIMARY KEY (topic_id, tag_id);


--
-- Name: topics topics_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.topics
    ADD CONSTRAINT topics_pkey PRIMARY KEY (id);


--
-- Name: user_achievements user_achievements_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.user_achievements
    ADD CONSTRAINT user_achievements_pkey PRIMARY KEY (user_id, achievement_id);


--
-- Name: user_certificates user_certificates_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.user_certificates
    ADD CONSTRAINT user_certificates_pkey PRIMARY KEY (id);


--
-- Name: user_profiles user_profiles_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.user_profiles
    ADD CONSTRAINT user_profiles_pkey PRIMARY KEY (user_id);


--
-- Name: user_rank_progress user_rank_progress_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.user_rank_progress
    ADD CONSTRAINT user_rank_progress_pkey PRIMARY KEY (user_id);


--
-- Name: user_ranks user_ranks_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.user_ranks
    ADD CONSTRAINT user_ranks_pkey PRIMARY KEY (id);


--
-- Name: users users_email_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.users
    ADD CONSTRAINT users_email_key UNIQUE (email);


--
-- Name: users users_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.users
    ADD CONSTRAINT users_pkey PRIMARY KEY (id);


--
-- Name: users users_username_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.users
    ADD CONSTRAINT users_username_key UNIQUE (username);


--
-- Name: GadukaGang__content_72eb3e_idx; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX "GadukaGang__content_72eb3e_idx" ON public."GadukaGang_searchindex" USING btree (content_type, object_id);


--
-- Name: GadukaGang_adminlog_admin_id_73248f79; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX "GadukaGang_adminlog_admin_id_73248f79" ON public."GadukaGang_adminlog" USING btree (admin_id);


--
-- Name: GadukaGang_chat_created_by_id_ac96fd34; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX "GadukaGang_chat_created_by_id_ac96fd34" ON public."GadukaGang_chat" USING btree (created_by_id);


--
-- Name: GadukaGang_chatmessage_chat_id_98d41dff; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX "GadukaGang_chatmessage_chat_id_98d41dff" ON public."GadukaGang_chatmessage" USING btree (chat_id);


--
-- Name: GadukaGang_chatmessage_sender_id_77929ccc; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX "GadukaGang_chatmessage_sender_id_77929ccc" ON public."GadukaGang_chatmessage" USING btree (sender_id);


--
-- Name: GadukaGang_chatparticipant_chat_id_95e8efcc; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX "GadukaGang_chatparticipant_chat_id_95e8efcc" ON public."GadukaGang_chatparticipant" USING btree (chat_id);


--
-- Name: GadukaGang_chatparticipant_user_id_c3e928da; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX "GadukaGang_chatparticipant_user_id_c3e928da" ON public."GadukaGang_chatparticipant" USING btree (user_id);


--
-- Name: GadukaGang_community_creator_id_dc5c7693; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX "GadukaGang_community_creator_id_dc5c7693" ON public."GadukaGang_community" USING btree (creator_id);


--
-- Name: GadukaGang_community_invite_token_fd9613cd_like; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX "GadukaGang_community_invite_token_fd9613cd_like" ON public."GadukaGang_community" USING btree (invite_token varchar_pattern_ops);


--
-- Name: GadukaGang_communitymembership_community_id_c2a98116; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX "GadukaGang_communitymembership_community_id_c2a98116" ON public."GadukaGang_communitymembership" USING btree (community_id);


--
-- Name: GadukaGang_communitymembership_user_id_36253129; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX "GadukaGang_communitymembership_user_id_36253129" ON public."GadukaGang_communitymembership" USING btree (user_id);


--
-- Name: GadukaGang_communitynotifi_community_id_afe59def; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX "GadukaGang_communitynotifi_community_id_afe59def" ON public."GadukaGang_communitynotificationsubscription" USING btree (community_id);


--
-- Name: GadukaGang_communitynotificationsubscription_user_id_ccf15706; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX "GadukaGang_communitynotificationsubscription_user_id_ccf15706" ON public."GadukaGang_communitynotificationsubscription" USING btree (user_id);


--
-- Name: GadukaGang_communitytopic_community_id_d4b25bc9; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX "GadukaGang_communitytopic_community_id_d4b25bc9" ON public."GadukaGang_communitytopic" USING btree (community_id);


--
-- Name: GadukaGang_communitytopic_topic_id_5120a67c; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX "GadukaGang_communitytopic_topic_id_5120a67c" ON public."GadukaGang_communitytopic" USING btree (topic_id);


--
-- Name: GadukaGang_complaint_assigned_moderator_id_789147c9; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX "GadukaGang_complaint_assigned_moderator_id_789147c9" ON public."GadukaGang_complaint" USING btree (assigned_moderator_id);


--
-- Name: GadukaGang_complaint_reporter_id_f4112b01; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX "GadukaGang_complaint_reporter_id_f4112b01" ON public."GadukaGang_complaint" USING btree (reporter_id);


--
-- Name: GadukaGang_courseprogress__courseprogress_id_b7fbadae; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX "GadukaGang_courseprogress__courseprogress_id_b7fbadae" ON public."GadukaGang_courseprogress_completed_lessons" USING btree (courseprogress_id);


--
-- Name: GadukaGang_courseprogress_completed_lessons_lesson_id_28ae6823; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX "GadukaGang_courseprogress_completed_lessons_lesson_id_28ae6823" ON public."GadukaGang_courseprogress_completed_lessons" USING btree (lesson_id);


--
-- Name: GadukaGang_courseprogress_course_id_f28bb5b1; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX "GadukaGang_courseprogress_course_id_f28bb5b1" ON public."GadukaGang_courseprogress" USING btree (course_id);


--
-- Name: GadukaGang_courseprogress_user_id_fbf4ce2f; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX "GadukaGang_courseprogress_user_id_fbf4ce2f" ON public."GadukaGang_courseprogress" USING btree (user_id);


--
-- Name: GadukaGang_forumsetting_modified_by_id_6258132e; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX "GadukaGang_forumsetting_modified_by_id_6258132e" ON public."GadukaGang_forumsetting" USING btree (modified_by_id);


--
-- Name: GadukaGang_forumsetting_setting_name_e86a815c_like; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX "GadukaGang_forumsetting_setting_name_e86a815c_like" ON public."GadukaGang_forumsetting" USING btree (setting_name varchar_pattern_ops);


--
-- Name: GadukaGang_githubauth_github_id_b4e79a7e_like; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX "GadukaGang_githubauth_github_id_b4e79a7e_like" ON public."GadukaGang_githubauth" USING btree (github_id varchar_pattern_ops);


--
-- Name: GadukaGang_lesson_course_id_dd26a4ca; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX "GadukaGang_lesson_course_id_dd26a4ca" ON public."GadukaGang_lesson" USING btree (course_id);


--
-- Name: GadukaGang_moderatoraction_moderator_id_7321cf15; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX "GadukaGang_moderatoraction_moderator_id_7321cf15" ON public."GadukaGang_moderatoraction" USING btree (moderator_id);


--
-- Name: GadukaGang_notification_user_id_37f93133; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX "GadukaGang_notification_user_id_37f93133" ON public."GadukaGang_notification" USING btree (user_id);


--
-- Name: GadukaGang_post_author_id_d7854ef7; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX "GadukaGang_post_author_id_d7854ef7" ON public."GadukaGang_post" USING btree (author_id);


--
-- Name: GadukaGang_post_topic_id_24dd03b6; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX "GadukaGang_post_topic_id_24dd03b6" ON public."GadukaGang_post" USING btree (topic_id);


--
-- Name: GadukaGang_postlike_post_id_0bd55c99; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX "GadukaGang_postlike_post_id_0bd55c99" ON public."GadukaGang_postlike" USING btree (post_id);


--
-- Name: GadukaGang_postlike_user_id_494d01c9; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX "GadukaGang_postlike_user_id_494d01c9" ON public."GadukaGang_postlike" USING btree (user_id);


--
-- Name: GadukaGang_section_created_by_id_16045d4f; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX "GadukaGang_section_created_by_id_16045d4f" ON public."GadukaGang_section" USING btree (created_by_id);


--
-- Name: GadukaGang_systemlog_user_id_c0323d0b; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX "GadukaGang_systemlog_user_id_c0323d0b" ON public."GadukaGang_systemlog" USING btree (user_id);


--
-- Name: GadukaGang_tag_name_f5179b6d_like; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX "GadukaGang_tag_name_f5179b6d_like" ON public."GadukaGang_tag" USING btree (name varchar_pattern_ops);


--
-- Name: GadukaGang_topic_author_id_aaf52abc; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX "GadukaGang_topic_author_id_aaf52abc" ON public."GadukaGang_topic" USING btree (author_id);


--
-- Name: GadukaGang_topic_section_id_ebc4d319; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX "GadukaGang_topic_section_id_ebc4d319" ON public."GadukaGang_topic" USING btree (section_id);


--
-- Name: GadukaGang_topicrating_topic_id_957a4f15; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX "GadukaGang_topicrating_topic_id_957a4f15" ON public."GadukaGang_topicrating" USING btree (topic_id);


--
-- Name: GadukaGang_topicrating_user_id_4a6f1932; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX "GadukaGang_topicrating_user_id_4a6f1932" ON public."GadukaGang_topicrating" USING btree (user_id);


--
-- Name: GadukaGang_topicsubscription_topic_id_037a1a88; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX "GadukaGang_topicsubscription_topic_id_037a1a88" ON public."GadukaGang_topicsubscription" USING btree (topic_id);


--
-- Name: GadukaGang_topicsubscription_user_id_36696fd4; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX "GadukaGang_topicsubscription_user_id_36696fd4" ON public."GadukaGang_topicsubscription" USING btree (user_id);


--
-- Name: GadukaGang_topictag_tag_id_3fec4224; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX "GadukaGang_topictag_tag_id_3fec4224" ON public."GadukaGang_topictag" USING btree (tag_id);


--
-- Name: GadukaGang_topictag_topic_id_f90c8485; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX "GadukaGang_topictag_topic_id_f90c8485" ON public."GadukaGang_topictag" USING btree (topic_id);


--
-- Name: GadukaGang_topicview_topic_id_67de75b0; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX "GadukaGang_topicview_topic_id_67de75b0" ON public."GadukaGang_topicview" USING btree (topic_id);


--
-- Name: GadukaGang_topicview_user_id_7a2d8093; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX "GadukaGang_topicview_user_id_7a2d8093" ON public."GadukaGang_topicview" USING btree (user_id);


--
-- Name: GadukaGang_user_groups_group_id_ed4afbb4; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX "GadukaGang_user_groups_group_id_ed4afbb4" ON public."GadukaGang_user_groups" USING btree (group_id);


--
-- Name: GadukaGang_user_groups_user_id_98a6e3ab; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX "GadukaGang_user_groups_user_id_98a6e3ab" ON public."GadukaGang_user_groups" USING btree (user_id);


--
-- Name: GadukaGang_user_user_permissions_permission_id_ee97d7c9; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX "GadukaGang_user_user_permissions_permission_id_ee97d7c9" ON public."GadukaGang_user_user_permissions" USING btree (permission_id);


--
-- Name: GadukaGang_user_user_permissions_user_id_293b6010; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX "GadukaGang_user_user_permissions_user_id_293b6010" ON public."GadukaGang_user_user_permissions" USING btree (user_id);


--
-- Name: GadukaGang_user_username_9c76d7e7_like; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX "GadukaGang_user_username_9c76d7e7_like" ON public."GadukaGang_user" USING btree (username varchar_pattern_ops);


--
-- Name: GadukaGang_userachievement_achievement_id_c686cde9; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX "GadukaGang_userachievement_achievement_id_c686cde9" ON public."GadukaGang_userachievement" USING btree (achievement_id);


--
-- Name: GadukaGang_userachievement_awarded_by_id_f2d2784e; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX "GadukaGang_userachievement_awarded_by_id_f2d2784e" ON public."GadukaGang_userachievement" USING btree (awarded_by_id);


--
-- Name: GadukaGang_userachievement_user_id_557795a4; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX "GadukaGang_userachievement_user_id_557795a4" ON public."GadukaGang_userachievement" USING btree (user_id);


--
-- Name: GadukaGang_usercertificate_awarded_by_id_9f721dfd; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX "GadukaGang_usercertificate_awarded_by_id_9f721dfd" ON public."GadukaGang_usercertificate" USING btree (awarded_by_id);


--
-- Name: GadukaGang_usercertificate_certificate_id_2a5b8a28; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX "GadukaGang_usercertificate_certificate_id_2a5b8a28" ON public."GadukaGang_usercertificate" USING btree (certificate_id);


--
-- Name: GadukaGang_usercertificate_user_id_b3375bdc; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX "GadukaGang_usercertificate_user_id_b3375bdc" ON public."GadukaGang_usercertificate" USING btree (user_id);


--
-- Name: GadukaGang_userrankprogress_rank_id_242d0262; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX "GadukaGang_userrankprogress_rank_id_242d0262" ON public."GadukaGang_userrankprogress" USING btree (rank_id);


--
-- Name: GadukaGang_usersubscription_subscribed_to_id_191db9ea; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX "GadukaGang_usersubscription_subscribed_to_id_191db9ea" ON public."GadukaGang_usersubscription" USING btree (subscribed_to_id);


--
-- Name: GadukaGang_usersubscription_subscriber_id_1ad78575; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX "GadukaGang_usersubscription_subscriber_id_1ad78575" ON public."GadukaGang_usersubscription" USING btree (subscriber_id);


--
-- Name: account_emailaddress_upper; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX account_emailaddress_upper ON public.account_emailaddress USING btree (upper((email)::text));


--
-- Name: account_emailaddress_user_id_2c513194; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX account_emailaddress_user_id_2c513194 ON public.account_emailaddress USING btree (user_id);


--
-- Name: account_emailconfirmation_email_address_id_5b7f8c58; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX account_emailconfirmation_email_address_id_5b7f8c58 ON public.account_emailconfirmation USING btree (email_address_id);


--
-- Name: account_emailconfirmation_key_f43612bd_like; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX account_emailconfirmation_key_f43612bd_like ON public.account_emailconfirmation USING btree (key varchar_pattern_ops);


--
-- Name: auth_group_name_a6ea08ec_like; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX auth_group_name_a6ea08ec_like ON public.auth_group USING btree (name varchar_pattern_ops);


--
-- Name: auth_group_permissions_group_id_b120cbf9; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX auth_group_permissions_group_id_b120cbf9 ON public.auth_group_permissions USING btree (group_id);


--
-- Name: auth_group_permissions_permission_id_84c5c92e; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX auth_group_permissions_permission_id_84c5c92e ON public.auth_group_permissions USING btree (permission_id);


--
-- Name: auth_permission_content_type_id_2f476e4b; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX auth_permission_content_type_id_2f476e4b ON public.auth_permission USING btree (content_type_id);


--
-- Name: authtoken_token_key_10f0b77e_like; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX authtoken_token_key_10f0b77e_like ON public.authtoken_token USING btree (key varchar_pattern_ops);


--
-- Name: django_admin_log_content_type_id_c4bce8eb; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX django_admin_log_content_type_id_c4bce8eb ON public.django_admin_log USING btree (content_type_id);


--
-- Name: django_admin_log_user_id_c564eba6; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX django_admin_log_user_id_c564eba6 ON public.django_admin_log USING btree (user_id);


--
-- Name: django_session_expire_date_a5c62663; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX django_session_expire_date_a5c62663 ON public.django_session USING btree (expire_date);


--
-- Name: django_session_session_key_c0390e0f_like; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX django_session_session_key_c0390e0f_like ON public.django_session USING btree (session_key varchar_pattern_ops);


--
-- Name: django_site_domain_a2e37b91_like; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX django_site_domain_a2e37b91_like ON public.django_site USING btree (domain varchar_pattern_ops);


--
-- Name: idx_chat_messages_chat; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_chat_messages_chat ON public.chat_messages USING btree (chat_id);


--
-- Name: idx_chat_messages_sender; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_chat_messages_sender ON public.chat_messages USING btree (sender_id);


--
-- Name: idx_complaints_moderator; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_complaints_moderator ON public.complaints USING btree (assigned_moderator);


--
-- Name: idx_complaints_status; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_complaints_status ON public.complaints USING btree (status);


--
-- Name: idx_posts_author; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_posts_author ON public.posts USING btree (author_id);


--
-- Name: idx_posts_created; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_posts_created ON public.posts USING btree (created_date);


--
-- Name: idx_posts_topic; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_posts_topic ON public.posts USING btree (topic_id);


--
-- Name: idx_system_logs_timestamp; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_system_logs_timestamp ON public.system_logs USING btree ("timestamp");


--
-- Name: idx_system_logs_user; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_system_logs_user ON public.system_logs USING btree (user_id);


--
-- Name: idx_topics_author; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_topics_author ON public.topics USING btree (author_id);


--
-- Name: idx_topics_section; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_topics_section ON public.topics USING btree (section_id);


--
-- Name: idx_users_email; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_users_email ON public.users USING btree (email);


--
-- Name: idx_users_username; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_users_username ON public.users USING btree (username);


--
-- Name: socialaccount_socialaccount_user_id_8146e70c; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX socialaccount_socialaccount_user_id_8146e70c ON public.socialaccount_socialaccount USING btree (user_id);


--
-- Name: socialaccount_socialapp_sites_site_id_2579dee5; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX socialaccount_socialapp_sites_site_id_2579dee5 ON public.socialaccount_socialapp_sites USING btree (site_id);


--
-- Name: socialaccount_socialapp_sites_socialapp_id_97fb6e7d; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX socialaccount_socialapp_sites_socialapp_id_97fb6e7d ON public.socialaccount_socialapp_sites USING btree (socialapp_id);


--
-- Name: socialaccount_socialtoken_account_id_951f210e; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX socialaccount_socialtoken_account_id_951f210e ON public.socialaccount_socialtoken USING btree (account_id);


--
-- Name: socialaccount_socialtoken_app_id_636a42d7; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX socialaccount_socialtoken_app_id_636a42d7 ON public.socialaccount_socialtoken USING btree (app_id);


--
-- Name: unique_verified_email; Type: INDEX; Schema: public; Owner: -
--

CREATE UNIQUE INDEX unique_verified_email ON public.account_emailaddress USING btree (email) WHERE verified;


--
-- Name: GadukaGang_moderatoraction trigger_audit_moderator_actions; Type: TRIGGER; Schema: public; Owner: -
--

CREATE TRIGGER trigger_audit_moderator_actions AFTER INSERT ON public."GadukaGang_moderatoraction" FOR EACH ROW EXECUTE FUNCTION public.audit_moderator_actions();


--
-- Name: GadukaGang_post trigger_audit_post_changes; Type: TRIGGER; Schema: public; Owner: -
--

CREATE TRIGGER trigger_audit_post_changes AFTER UPDATE ON public."GadukaGang_post" FOR EACH ROW EXECUTE FUNCTION public.audit_post_changes();


--
-- Name: GadukaGang_user trigger_audit_user_changes; Type: TRIGGER; Schema: public; Owner: -
--

CREATE TRIGGER trigger_audit_user_changes AFTER DELETE OR UPDATE ON public."GadukaGang_user" FOR EACH ROW EXECUTE FUNCTION public.audit_user_changes();


--
-- Name: GadukaGang_userachievement trigger_award_points_for_achievement; Type: TRIGGER; Schema: public; Owner: -
--

CREATE TRIGGER trigger_award_points_for_achievement AFTER INSERT ON public."GadukaGang_userachievement" FOR EACH ROW EXECUTE FUNCTION public.award_points_for_achievement();


--
-- Name: GadukaGang_post trigger_update_last_activity_on_post; Type: TRIGGER; Schema: public; Owner: -
--

CREATE TRIGGER trigger_update_last_activity_on_post AFTER INSERT OR UPDATE ON public."GadukaGang_post" FOR EACH ROW EXECUTE FUNCTION public.update_user_last_activity();


--
-- Name: GadukaGang_post trigger_update_post_count; Type: TRIGGER; Schema: public; Owner: -
--

CREATE TRIGGER trigger_update_post_count AFTER INSERT OR DELETE OR UPDATE ON public."GadukaGang_post" FOR EACH ROW EXECUTE FUNCTION public.update_post_count();


--
-- Name: GadukaGang_post trigger_update_topic_last_post; Type: TRIGGER; Schema: public; Owner: -
--

CREATE TRIGGER trigger_update_topic_last_post AFTER INSERT ON public."GadukaGang_post" FOR EACH ROW EXECUTE FUNCTION public.update_topic_last_post();


--
-- Name: posts trigger_update_topic_last_post_date; Type: TRIGGER; Schema: public; Owner: -
--

CREATE TRIGGER trigger_update_topic_last_post_date AFTER INSERT ON public.posts FOR EACH ROW EXECUTE FUNCTION public.update_topic_last_post_date();


--
-- Name: posts trigger_update_user_post_count; Type: TRIGGER; Schema: public; Owner: -
--

CREATE TRIGGER trigger_update_user_post_count AFTER INSERT OR DELETE ON public.posts FOR EACH ROW EXECUTE FUNCTION public.update_user_post_count();


--
-- Name: GadukaGang_usersubscription trigger_validate_subscription; Type: TRIGGER; Schema: public; Owner: -
--

CREATE TRIGGER trigger_validate_subscription BEFORE INSERT OR UPDATE ON public."GadukaGang_usersubscription" FOR EACH ROW EXECUTE FUNCTION public.validate_subscription();


--
-- Name: GadukaGang_adminlog GadukaGang_adminlog_admin_id_73248f79_fk_GadukaGang_user_id; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public."GadukaGang_adminlog"
    ADD CONSTRAINT "GadukaGang_adminlog_admin_id_73248f79_fk_GadukaGang_user_id" FOREIGN KEY (admin_id) REFERENCES public."GadukaGang_user"(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: GadukaGang_chat GadukaGang_chat_created_by_id_ac96fd34_fk_GadukaGang_user_id; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public."GadukaGang_chat"
    ADD CONSTRAINT "GadukaGang_chat_created_by_id_ac96fd34_fk_GadukaGang_user_id" FOREIGN KEY (created_by_id) REFERENCES public."GadukaGang_user"(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: GadukaGang_chatmessage GadukaGang_chatmessage_chat_id_98d41dff_fk_GadukaGang_chat_id; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public."GadukaGang_chatmessage"
    ADD CONSTRAINT "GadukaGang_chatmessage_chat_id_98d41dff_fk_GadukaGang_chat_id" FOREIGN KEY (chat_id) REFERENCES public."GadukaGang_chat"(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: GadukaGang_chatmessage GadukaGang_chatmessage_sender_id_77929ccc_fk_GadukaGang_user_id; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public."GadukaGang_chatmessage"
    ADD CONSTRAINT "GadukaGang_chatmessage_sender_id_77929ccc_fk_GadukaGang_user_id" FOREIGN KEY (sender_id) REFERENCES public."GadukaGang_user"(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: GadukaGang_chatparticipant GadukaGang_chatparti_chat_id_95e8efcc_fk_GadukaGan; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public."GadukaGang_chatparticipant"
    ADD CONSTRAINT "GadukaGang_chatparti_chat_id_95e8efcc_fk_GadukaGan" FOREIGN KEY (chat_id) REFERENCES public."GadukaGang_chat"(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: GadukaGang_chatparticipant GadukaGang_chatparti_user_id_c3e928da_fk_GadukaGan; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public."GadukaGang_chatparticipant"
    ADD CONSTRAINT "GadukaGang_chatparti_user_id_c3e928da_fk_GadukaGan" FOREIGN KEY (user_id) REFERENCES public."GadukaGang_user"(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: GadukaGang_communitynotificationsubscription GadukaGang_community_community_id_afe59def_fk_GadukaGan; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public."GadukaGang_communitynotificationsubscription"
    ADD CONSTRAINT "GadukaGang_community_community_id_afe59def_fk_GadukaGan" FOREIGN KEY (community_id) REFERENCES public."GadukaGang_community"(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: GadukaGang_communitymembership GadukaGang_community_community_id_c2a98116_fk_GadukaGan; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public."GadukaGang_communitymembership"
    ADD CONSTRAINT "GadukaGang_community_community_id_c2a98116_fk_GadukaGan" FOREIGN KEY (community_id) REFERENCES public."GadukaGang_community"(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: GadukaGang_communitytopic GadukaGang_community_community_id_d4b25bc9_fk_GadukaGan; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public."GadukaGang_communitytopic"
    ADD CONSTRAINT "GadukaGang_community_community_id_d4b25bc9_fk_GadukaGan" FOREIGN KEY (community_id) REFERENCES public."GadukaGang_community"(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: GadukaGang_community GadukaGang_community_creator_id_dc5c7693_fk_GadukaGang_user_id; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public."GadukaGang_community"
    ADD CONSTRAINT "GadukaGang_community_creator_id_dc5c7693_fk_GadukaGang_user_id" FOREIGN KEY (creator_id) REFERENCES public."GadukaGang_user"(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: GadukaGang_communitytopic GadukaGang_community_topic_id_5120a67c_fk_GadukaGan; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public."GadukaGang_communitytopic"
    ADD CONSTRAINT "GadukaGang_community_topic_id_5120a67c_fk_GadukaGan" FOREIGN KEY (topic_id) REFERENCES public."GadukaGang_topic"(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: GadukaGang_communitymembership GadukaGang_community_user_id_36253129_fk_GadukaGan; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public."GadukaGang_communitymembership"
    ADD CONSTRAINT "GadukaGang_community_user_id_36253129_fk_GadukaGan" FOREIGN KEY (user_id) REFERENCES public."GadukaGang_user"(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: GadukaGang_communitynotificationsubscription GadukaGang_community_user_id_ccf15706_fk_GadukaGan; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public."GadukaGang_communitynotificationsubscription"
    ADD CONSTRAINT "GadukaGang_community_user_id_ccf15706_fk_GadukaGan" FOREIGN KEY (user_id) REFERENCES public."GadukaGang_user"(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: GadukaGang_complaint GadukaGang_complaint_assigned_moderator_i_789147c9_fk_GadukaGan; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public."GadukaGang_complaint"
    ADD CONSTRAINT "GadukaGang_complaint_assigned_moderator_i_789147c9_fk_GadukaGan" FOREIGN KEY (assigned_moderator_id) REFERENCES public."GadukaGang_user"(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: GadukaGang_complaint GadukaGang_complaint_reporter_id_f4112b01_fk_GadukaGang_user_id; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public."GadukaGang_complaint"
    ADD CONSTRAINT "GadukaGang_complaint_reporter_id_f4112b01_fk_GadukaGang_user_id" FOREIGN KEY (reporter_id) REFERENCES public."GadukaGang_user"(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: GadukaGang_courseprogress GadukaGang_coursepro_course_id_f28bb5b1_fk_GadukaGan; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public."GadukaGang_courseprogress"
    ADD CONSTRAINT "GadukaGang_coursepro_course_id_f28bb5b1_fk_GadukaGan" FOREIGN KEY (course_id) REFERENCES public."GadukaGang_course"(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: GadukaGang_courseprogress_completed_lessons GadukaGang_coursepro_courseprogress_id_b7fbadae_fk_GadukaGan; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public."GadukaGang_courseprogress_completed_lessons"
    ADD CONSTRAINT "GadukaGang_coursepro_courseprogress_id_b7fbadae_fk_GadukaGan" FOREIGN KEY (courseprogress_id) REFERENCES public."GadukaGang_courseprogress"(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: GadukaGang_courseprogress_completed_lessons GadukaGang_coursepro_lesson_id_28ae6823_fk_GadukaGan; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public."GadukaGang_courseprogress_completed_lessons"
    ADD CONSTRAINT "GadukaGang_coursepro_lesson_id_28ae6823_fk_GadukaGan" FOREIGN KEY (lesson_id) REFERENCES public."GadukaGang_lesson"(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: GadukaGang_courseprogress GadukaGang_coursepro_user_id_fbf4ce2f_fk_GadukaGan; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public."GadukaGang_courseprogress"
    ADD CONSTRAINT "GadukaGang_coursepro_user_id_fbf4ce2f_fk_GadukaGan" FOREIGN KEY (user_id) REFERENCES public."GadukaGang_user"(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: GadukaGang_forumsetting GadukaGang_forumsett_modified_by_id_6258132e_fk_GadukaGan; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public."GadukaGang_forumsetting"
    ADD CONSTRAINT "GadukaGang_forumsett_modified_by_id_6258132e_fk_GadukaGan" FOREIGN KEY (modified_by_id) REFERENCES public."GadukaGang_user"(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: GadukaGang_githubauth GadukaGang_githubauth_user_id_46526e70_fk_GadukaGang_user_id; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public."GadukaGang_githubauth"
    ADD CONSTRAINT "GadukaGang_githubauth_user_id_46526e70_fk_GadukaGang_user_id" FOREIGN KEY (user_id) REFERENCES public."GadukaGang_user"(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: GadukaGang_lesson GadukaGang_lesson_course_id_dd26a4ca_fk_GadukaGang_course_id; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public."GadukaGang_lesson"
    ADD CONSTRAINT "GadukaGang_lesson_course_id_dd26a4ca_fk_GadukaGang_course_id" FOREIGN KEY (course_id) REFERENCES public."GadukaGang_course"(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: GadukaGang_moderatoraction GadukaGang_moderator_moderator_id_7321cf15_fk_GadukaGan; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public."GadukaGang_moderatoraction"
    ADD CONSTRAINT "GadukaGang_moderator_moderator_id_7321cf15_fk_GadukaGan" FOREIGN KEY (moderator_id) REFERENCES public."GadukaGang_user"(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: GadukaGang_notification GadukaGang_notification_user_id_37f93133_fk_GadukaGang_user_id; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public."GadukaGang_notification"
    ADD CONSTRAINT "GadukaGang_notification_user_id_37f93133_fk_GadukaGang_user_id" FOREIGN KEY (user_id) REFERENCES public."GadukaGang_user"(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: GadukaGang_post GadukaGang_post_author_id_d7854ef7_fk_GadukaGang_user_id; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public."GadukaGang_post"
    ADD CONSTRAINT "GadukaGang_post_author_id_d7854ef7_fk_GadukaGang_user_id" FOREIGN KEY (author_id) REFERENCES public."GadukaGang_user"(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: GadukaGang_post GadukaGang_post_topic_id_24dd03b6_fk_GadukaGang_topic_id; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public."GadukaGang_post"
    ADD CONSTRAINT "GadukaGang_post_topic_id_24dd03b6_fk_GadukaGang_topic_id" FOREIGN KEY (topic_id) REFERENCES public."GadukaGang_topic"(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: GadukaGang_postlike GadukaGang_postlike_post_id_0bd55c99_fk_GadukaGang_post_id; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public."GadukaGang_postlike"
    ADD CONSTRAINT "GadukaGang_postlike_post_id_0bd55c99_fk_GadukaGang_post_id" FOREIGN KEY (post_id) REFERENCES public."GadukaGang_post"(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: GadukaGang_postlike GadukaGang_postlike_user_id_494d01c9_fk_GadukaGang_user_id; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public."GadukaGang_postlike"
    ADD CONSTRAINT "GadukaGang_postlike_user_id_494d01c9_fk_GadukaGang_user_id" FOREIGN KEY (user_id) REFERENCES public."GadukaGang_user"(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: GadukaGang_section GadukaGang_section_created_by_id_16045d4f_fk_GadukaGang_user_id; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public."GadukaGang_section"
    ADD CONSTRAINT "GadukaGang_section_created_by_id_16045d4f_fk_GadukaGang_user_id" FOREIGN KEY (created_by_id) REFERENCES public."GadukaGang_user"(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: GadukaGang_systemlog GadukaGang_systemlog_user_id_c0323d0b_fk_GadukaGang_user_id; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public."GadukaGang_systemlog"
    ADD CONSTRAINT "GadukaGang_systemlog_user_id_c0323d0b_fk_GadukaGang_user_id" FOREIGN KEY (user_id) REFERENCES public."GadukaGang_user"(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: GadukaGang_topic GadukaGang_topic_author_id_aaf52abc_fk_GadukaGang_user_id; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public."GadukaGang_topic"
    ADD CONSTRAINT "GadukaGang_topic_author_id_aaf52abc_fk_GadukaGang_user_id" FOREIGN KEY (author_id) REFERENCES public."GadukaGang_user"(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: GadukaGang_topic GadukaGang_topic_section_id_ebc4d319_fk_GadukaGang_section_id; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public."GadukaGang_topic"
    ADD CONSTRAINT "GadukaGang_topic_section_id_ebc4d319_fk_GadukaGang_section_id" FOREIGN KEY (section_id) REFERENCES public."GadukaGang_section"(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: GadukaGang_topicrating GadukaGang_topicrating_topic_id_957a4f15_fk_GadukaGang_topic_id; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public."GadukaGang_topicrating"
    ADD CONSTRAINT "GadukaGang_topicrating_topic_id_957a4f15_fk_GadukaGang_topic_id" FOREIGN KEY (topic_id) REFERENCES public."GadukaGang_topic"(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: GadukaGang_topicrating GadukaGang_topicrating_user_id_4a6f1932_fk_GadukaGang_user_id; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public."GadukaGang_topicrating"
    ADD CONSTRAINT "GadukaGang_topicrating_user_id_4a6f1932_fk_GadukaGang_user_id" FOREIGN KEY (user_id) REFERENCES public."GadukaGang_user"(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: GadukaGang_topicsubscription GadukaGang_topicsubs_topic_id_037a1a88_fk_GadukaGan; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public."GadukaGang_topicsubscription"
    ADD CONSTRAINT "GadukaGang_topicsubs_topic_id_037a1a88_fk_GadukaGan" FOREIGN KEY (topic_id) REFERENCES public."GadukaGang_topic"(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: GadukaGang_topicsubscription GadukaGang_topicsubs_user_id_36696fd4_fk_GadukaGan; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public."GadukaGang_topicsubscription"
    ADD CONSTRAINT "GadukaGang_topicsubs_user_id_36696fd4_fk_GadukaGan" FOREIGN KEY (user_id) REFERENCES public."GadukaGang_user"(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: GadukaGang_topictag GadukaGang_topictag_tag_id_3fec4224_fk_GadukaGang_tag_id; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public."GadukaGang_topictag"
    ADD CONSTRAINT "GadukaGang_topictag_tag_id_3fec4224_fk_GadukaGang_tag_id" FOREIGN KEY (tag_id) REFERENCES public."GadukaGang_tag"(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: GadukaGang_topictag GadukaGang_topictag_topic_id_f90c8485_fk_GadukaGang_topic_id; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public."GadukaGang_topictag"
    ADD CONSTRAINT "GadukaGang_topictag_topic_id_f90c8485_fk_GadukaGang_topic_id" FOREIGN KEY (topic_id) REFERENCES public."GadukaGang_topic"(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: GadukaGang_topicview GadukaGang_topicview_topic_id_67de75b0_fk_GadukaGang_topic_id; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public."GadukaGang_topicview"
    ADD CONSTRAINT "GadukaGang_topicview_topic_id_67de75b0_fk_GadukaGang_topic_id" FOREIGN KEY (topic_id) REFERENCES public."GadukaGang_topic"(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: GadukaGang_topicview GadukaGang_topicview_user_id_7a2d8093_fk_GadukaGang_user_id; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public."GadukaGang_topicview"
    ADD CONSTRAINT "GadukaGang_topicview_user_id_7a2d8093_fk_GadukaGang_user_id" FOREIGN KEY (user_id) REFERENCES public."GadukaGang_user"(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: GadukaGang_user_groups GadukaGang_user_groups_group_id_ed4afbb4_fk_auth_group_id; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public."GadukaGang_user_groups"
    ADD CONSTRAINT "GadukaGang_user_groups_group_id_ed4afbb4_fk_auth_group_id" FOREIGN KEY (group_id) REFERENCES public.auth_group(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: GadukaGang_user_groups GadukaGang_user_groups_user_id_98a6e3ab_fk_GadukaGang_user_id; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public."GadukaGang_user_groups"
    ADD CONSTRAINT "GadukaGang_user_groups_user_id_98a6e3ab_fk_GadukaGang_user_id" FOREIGN KEY (user_id) REFERENCES public."GadukaGang_user"(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: GadukaGang_user_user_permissions GadukaGang_user_user_permission_id_ee97d7c9_fk_auth_perm; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public."GadukaGang_user_user_permissions"
    ADD CONSTRAINT "GadukaGang_user_user_permission_id_ee97d7c9_fk_auth_perm" FOREIGN KEY (permission_id) REFERENCES public.auth_permission(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: GadukaGang_user_user_permissions GadukaGang_user_user_user_id_293b6010_fk_GadukaGan; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public."GadukaGang_user_user_permissions"
    ADD CONSTRAINT "GadukaGang_user_user_user_id_293b6010_fk_GadukaGan" FOREIGN KEY (user_id) REFERENCES public."GadukaGang_user"(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: GadukaGang_userachievement GadukaGang_userachie_achievement_id_c686cde9_fk_GadukaGan; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public."GadukaGang_userachievement"
    ADD CONSTRAINT "GadukaGang_userachie_achievement_id_c686cde9_fk_GadukaGan" FOREIGN KEY (achievement_id) REFERENCES public."GadukaGang_achievement"(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: GadukaGang_userachievement GadukaGang_userachie_awarded_by_id_f2d2784e_fk_GadukaGan; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public."GadukaGang_userachievement"
    ADD CONSTRAINT "GadukaGang_userachie_awarded_by_id_f2d2784e_fk_GadukaGan" FOREIGN KEY (awarded_by_id) REFERENCES public."GadukaGang_user"(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: GadukaGang_userachievement GadukaGang_userachie_user_id_557795a4_fk_GadukaGan; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public."GadukaGang_userachievement"
    ADD CONSTRAINT "GadukaGang_userachie_user_id_557795a4_fk_GadukaGan" FOREIGN KEY (user_id) REFERENCES public."GadukaGang_user"(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: GadukaGang_usercertificate GadukaGang_usercerti_awarded_by_id_9f721dfd_fk_GadukaGan; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public."GadukaGang_usercertificate"
    ADD CONSTRAINT "GadukaGang_usercerti_awarded_by_id_9f721dfd_fk_GadukaGan" FOREIGN KEY (awarded_by_id) REFERENCES public."GadukaGang_user"(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: GadukaGang_usercertificate GadukaGang_usercerti_certificate_id_2a5b8a28_fk_GadukaGan; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public."GadukaGang_usercertificate"
    ADD CONSTRAINT "GadukaGang_usercerti_certificate_id_2a5b8a28_fk_GadukaGan" FOREIGN KEY (certificate_id) REFERENCES public."GadukaGang_certificate"(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: GadukaGang_usercertificate GadukaGang_usercerti_user_id_b3375bdc_fk_GadukaGan; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public."GadukaGang_usercertificate"
    ADD CONSTRAINT "GadukaGang_usercerti_user_id_b3375bdc_fk_GadukaGan" FOREIGN KEY (user_id) REFERENCES public."GadukaGang_user"(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: GadukaGang_userprofile GadukaGang_userprofile_user_id_6018d8a9_fk_GadukaGang_user_id; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public."GadukaGang_userprofile"
    ADD CONSTRAINT "GadukaGang_userprofile_user_id_6018d8a9_fk_GadukaGang_user_id" FOREIGN KEY (user_id) REFERENCES public."GadukaGang_user"(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: GadukaGang_userrankprogress GadukaGang_userrankp_rank_id_242d0262_fk_GadukaGan; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public."GadukaGang_userrankprogress"
    ADD CONSTRAINT "GadukaGang_userrankp_rank_id_242d0262_fk_GadukaGan" FOREIGN KEY (rank_id) REFERENCES public."GadukaGang_userrank"(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: GadukaGang_userrankprogress GadukaGang_userrankp_user_id_d3a2ca7b_fk_GadukaGan; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public."GadukaGang_userrankprogress"
    ADD CONSTRAINT "GadukaGang_userrankp_user_id_d3a2ca7b_fk_GadukaGan" FOREIGN KEY (user_id) REFERENCES public."GadukaGang_user"(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: GadukaGang_usersubscription GadukaGang_usersubsc_subscribed_to_id_191db9ea_fk_GadukaGan; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public."GadukaGang_usersubscription"
    ADD CONSTRAINT "GadukaGang_usersubsc_subscribed_to_id_191db9ea_fk_GadukaGan" FOREIGN KEY (subscribed_to_id) REFERENCES public."GadukaGang_user"(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: GadukaGang_usersubscription GadukaGang_usersubsc_subscriber_id_1ad78575_fk_GadukaGan; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public."GadukaGang_usersubscription"
    ADD CONSTRAINT "GadukaGang_usersubsc_subscriber_id_1ad78575_fk_GadukaGan" FOREIGN KEY (subscriber_id) REFERENCES public."GadukaGang_user"(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: account_emailaddress account_emailaddress_user_id_2c513194_fk_GadukaGang_user_id; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.account_emailaddress
    ADD CONSTRAINT "account_emailaddress_user_id_2c513194_fk_GadukaGang_user_id" FOREIGN KEY (user_id) REFERENCES public."GadukaGang_user"(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: account_emailconfirmation account_emailconfirm_email_address_id_5b7f8c58_fk_account_e; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.account_emailconfirmation
    ADD CONSTRAINT account_emailconfirm_email_address_id_5b7f8c58_fk_account_e FOREIGN KEY (email_address_id) REFERENCES public.account_emailaddress(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: auth_group_permissions auth_group_permissio_permission_id_84c5c92e_fk_auth_perm; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.auth_group_permissions
    ADD CONSTRAINT auth_group_permissio_permission_id_84c5c92e_fk_auth_perm FOREIGN KEY (permission_id) REFERENCES public.auth_permission(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: auth_group_permissions auth_group_permissions_group_id_b120cbf9_fk_auth_group_id; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.auth_group_permissions
    ADD CONSTRAINT auth_group_permissions_group_id_b120cbf9_fk_auth_group_id FOREIGN KEY (group_id) REFERENCES public.auth_group(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: auth_permission auth_permission_content_type_id_2f476e4b_fk_django_co; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.auth_permission
    ADD CONSTRAINT auth_permission_content_type_id_2f476e4b_fk_django_co FOREIGN KEY (content_type_id) REFERENCES public.django_content_type(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: authtoken_token authtoken_token_user_id_35299eff_fk_GadukaGang_user_id; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.authtoken_token
    ADD CONSTRAINT "authtoken_token_user_id_35299eff_fk_GadukaGang_user_id" FOREIGN KEY (user_id) REFERENCES public."GadukaGang_user"(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: chat_messages chat_messages_chat_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.chat_messages
    ADD CONSTRAINT chat_messages_chat_id_fkey FOREIGN KEY (chat_id) REFERENCES public.chats(id) ON DELETE CASCADE;


--
-- Name: chat_messages chat_messages_sender_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.chat_messages
    ADD CONSTRAINT chat_messages_sender_id_fkey FOREIGN KEY (sender_id) REFERENCES public.users(id);


--
-- Name: chat_participants chat_participants_chat_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.chat_participants
    ADD CONSTRAINT chat_participants_chat_id_fkey FOREIGN KEY (chat_id) REFERENCES public.chats(id) ON DELETE CASCADE;


--
-- Name: chat_participants chat_participants_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.chat_participants
    ADD CONSTRAINT chat_participants_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id) ON DELETE CASCADE;


--
-- Name: chats chats_created_by_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.chats
    ADD CONSTRAINT chats_created_by_fkey FOREIGN KEY (created_by) REFERENCES public.users(id);


--
-- Name: complaints complaints_assigned_moderator_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.complaints
    ADD CONSTRAINT complaints_assigned_moderator_fkey FOREIGN KEY (assigned_moderator) REFERENCES public.users(id);


--
-- Name: complaints complaints_reporter_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.complaints
    ADD CONSTRAINT complaints_reporter_id_fkey FOREIGN KEY (reporter_id) REFERENCES public.users(id);


--
-- Name: django_admin_log django_admin_log_content_type_id_c4bce8eb_fk_django_co; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.django_admin_log
    ADD CONSTRAINT django_admin_log_content_type_id_c4bce8eb_fk_django_co FOREIGN KEY (content_type_id) REFERENCES public.django_content_type(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: django_admin_log django_admin_log_user_id_c564eba6_fk_GadukaGang_user_id; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.django_admin_log
    ADD CONSTRAINT "django_admin_log_user_id_c564eba6_fk_GadukaGang_user_id" FOREIGN KEY (user_id) REFERENCES public."GadukaGang_user"(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: forum_settings forum_settings_modified_by_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.forum_settings
    ADD CONSTRAINT forum_settings_modified_by_fkey FOREIGN KEY (modified_by) REFERENCES public.users(id);


--
-- Name: posts posts_author_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.posts
    ADD CONSTRAINT posts_author_id_fkey FOREIGN KEY (author_id) REFERENCES public.users(id);


--
-- Name: posts posts_topic_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.posts
    ADD CONSTRAINT posts_topic_id_fkey FOREIGN KEY (topic_id) REFERENCES public.topics(id) ON DELETE CASCADE;


--
-- Name: sections sections_created_by_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.sections
    ADD CONSTRAINT sections_created_by_fkey FOREIGN KEY (created_by) REFERENCES public.users(id);


--
-- Name: socialaccount_socialtoken socialaccount_social_account_id_951f210e_fk_socialacc; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.socialaccount_socialtoken
    ADD CONSTRAINT socialaccount_social_account_id_951f210e_fk_socialacc FOREIGN KEY (account_id) REFERENCES public.socialaccount_socialaccount(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: socialaccount_socialtoken socialaccount_social_app_id_636a42d7_fk_socialacc; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.socialaccount_socialtoken
    ADD CONSTRAINT socialaccount_social_app_id_636a42d7_fk_socialacc FOREIGN KEY (app_id) REFERENCES public.socialaccount_socialapp(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: socialaccount_socialapp_sites socialaccount_social_site_id_2579dee5_fk_django_si; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.socialaccount_socialapp_sites
    ADD CONSTRAINT socialaccount_social_site_id_2579dee5_fk_django_si FOREIGN KEY (site_id) REFERENCES public.django_site(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: socialaccount_socialapp_sites socialaccount_social_socialapp_id_97fb6e7d_fk_socialacc; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.socialaccount_socialapp_sites
    ADD CONSTRAINT socialaccount_social_socialapp_id_97fb6e7d_fk_socialacc FOREIGN KEY (socialapp_id) REFERENCES public.socialaccount_socialapp(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: socialaccount_socialaccount socialaccount_social_user_id_8146e70c_fk_GadukaGan; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.socialaccount_socialaccount
    ADD CONSTRAINT "socialaccount_social_user_id_8146e70c_fk_GadukaGan" FOREIGN KEY (user_id) REFERENCES public."GadukaGang_user"(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: system_logs system_logs_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.system_logs
    ADD CONSTRAINT system_logs_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id);


--
-- Name: topic_tags topic_tags_tag_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.topic_tags
    ADD CONSTRAINT topic_tags_tag_id_fkey FOREIGN KEY (tag_id) REFERENCES public.tags(id) ON DELETE CASCADE;


--
-- Name: topic_tags topic_tags_topic_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.topic_tags
    ADD CONSTRAINT topic_tags_topic_id_fkey FOREIGN KEY (topic_id) REFERENCES public.topics(id) ON DELETE CASCADE;


--
-- Name: topics topics_author_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.topics
    ADD CONSTRAINT topics_author_id_fkey FOREIGN KEY (author_id) REFERENCES public.users(id);


--
-- Name: topics topics_section_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.topics
    ADD CONSTRAINT topics_section_id_fkey FOREIGN KEY (section_id) REFERENCES public.sections(id) ON DELETE CASCADE;


--
-- Name: user_achievements user_achievements_achievement_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.user_achievements
    ADD CONSTRAINT user_achievements_achievement_id_fkey FOREIGN KEY (achievement_id) REFERENCES public.achievements(id) ON DELETE CASCADE;


--
-- Name: user_achievements user_achievements_awarded_by_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.user_achievements
    ADD CONSTRAINT user_achievements_awarded_by_fkey FOREIGN KEY (awarded_by) REFERENCES public.users(id);


--
-- Name: user_achievements user_achievements_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.user_achievements
    ADD CONSTRAINT user_achievements_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id) ON DELETE CASCADE;


--
-- Name: user_certificates user_certificates_awarded_by_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.user_certificates
    ADD CONSTRAINT user_certificates_awarded_by_fkey FOREIGN KEY (awarded_by) REFERENCES public.users(id);


--
-- Name: user_certificates user_certificates_certificate_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.user_certificates
    ADD CONSTRAINT user_certificates_certificate_id_fkey FOREIGN KEY (certificate_id) REFERENCES public.certificates(id);


--
-- Name: user_certificates user_certificates_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.user_certificates
    ADD CONSTRAINT user_certificates_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id) ON DELETE CASCADE;


--
-- Name: user_profiles user_profiles_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.user_profiles
    ADD CONSTRAINT user_profiles_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id) ON DELETE CASCADE;


--
-- Name: user_rank_progress user_rank_progress_rank_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.user_rank_progress
    ADD CONSTRAINT user_rank_progress_rank_id_fkey FOREIGN KEY (rank_id) REFERENCES public.user_ranks(id);


--
-- Name: user_rank_progress user_rank_progress_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.user_rank_progress
    ADD CONSTRAINT user_rank_progress_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id) ON DELETE CASCADE;


--
-- PostgreSQL database dump complete
--

