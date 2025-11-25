-- ============================================
-- ТРИГГЕРЫ ДЛЯ АУДИТА (Audit Triggers)
-- ============================================

-- 1. Триггер аудита изменений пользователей
CREATE OR REPLACE FUNCTION audit_user_changes()
RETURNS TRIGGER AS $$
BEGIN
    IF (TG_OP = 'UPDATE') THEN
        -- Логируем изменение роли
        IF OLD.role != NEW.role THEN
            INSERT INTO system_logs (
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
            INSERT INTO system_logs (
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
        INSERT INTO system_logs (
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
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trigger_audit_user_changes ON users;
CREATE TRIGGER trigger_audit_user_changes
AFTER UPDATE OR DELETE ON users
FOR EACH ROW
EXECUTE FUNCTION audit_user_changes();

-- 2. Триггер аудита изменений постов
CREATE OR REPLACE FUNCTION audit_post_changes()
RETURNS TRIGGER AS $$
BEGIN
    IF (TG_OP = 'UPDATE') THEN
        -- Логируем редактирование контента
        IF OLD.content != NEW.content THEN
            INSERT INTO system_logs (
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
                'user'::user_role_enum,
                'Пост #' || NEW.id || ' отредактирован (редакция #' || NEW.edit_count || ')',
                'post',
                NEW.id,
                CURRENT_TIMESTAMP
            );
        END IF;
        
        -- Логируем удаление
        IF OLD.is_deleted = FALSE AND NEW.is_deleted = TRUE THEN
            INSERT INTO system_logs (
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
                'user'::user_role_enum,
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
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trigger_audit_post_changes ON posts;
CREATE TRIGGER trigger_audit_post_changes
AFTER UPDATE ON posts
FOR EACH ROW
EXECUTE FUNCTION audit_post_changes();

-- 3. Триггер автообновления last_activity
CREATE OR REPLACE FUNCTION update_user_last_activity()
RETURNS TRIGGER AS $$
BEGIN
    IF (TG_OP = 'INSERT' OR TG_OP = 'UPDATE') THEN
        UPDATE user_profiles
        SET last_activity = CURRENT_TIMESTAMP
        WHERE user_id = NEW.author_id;
        RETURN NEW;
    END IF;
    RETURN NULL;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trigger_update_last_activity_on_post ON posts;
CREATE TRIGGER trigger_update_last_activity_on_post
AFTER INSERT OR UPDATE ON posts
FOR EACH ROW
EXECUTE FUNCTION update_user_last_activity();

-- 4. Триггер обновления счётчика постов
CREATE OR REPLACE FUNCTION update_post_count()
RETURNS TRIGGER AS $$
BEGIN
    IF (TG_OP = 'INSERT') THEN
        UPDATE user_profiles
        SET post_count = post_count + 1
        WHERE user_id = NEW.author_id;
        RETURN NEW;
    ELSIF (TG_OP = 'DELETE') THEN
        UPDATE user_profiles
        SET post_count = GREATEST(0, post_count - 1)
        WHERE user_id = OLD.author_id;
        RETURN OLD;
    ELSIF (TG_OP = 'UPDATE') THEN
        -- Если пост помечен как удалённый
        IF OLD.is_deleted = FALSE AND NEW.is_deleted = TRUE THEN
            UPDATE user_profiles
            SET post_count = GREATEST(0, post_count - 1)
            WHERE user_id = NEW.author_id;
        ELSIF OLD.is_deleted = TRUE AND NEW.is_deleted = FALSE THEN
            UPDATE user_profiles
            SET post_count = post_count + 1
            WHERE user_id = NEW.author_id;
        END IF;
        RETURN NEW;
    END IF;
    RETURN NULL;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trigger_update_post_count ON posts;
CREATE TRIGGER trigger_update_post_count
AFTER INSERT OR DELETE OR UPDATE ON posts
FOR EACH ROW
EXECUTE FUNCTION update_post_count();

-- 5. Триггер обновления даты последнего поста в теме
CREATE OR REPLACE FUNCTION update_topic_last_post()
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

DROP TRIGGER IF EXISTS trigger_update_topic_last_post ON posts;
CREATE TRIGGER trigger_update_topic_last_post
AFTER INSERT ON posts
FOR EACH ROW
EXECUTE FUNCTION update_topic_last_post();

-- 6. Триггер аудита действий модераторов
CREATE OR REPLACE FUNCTION audit_moderator_actions()
RETURNS TRIGGER AS $$
BEGIN
    IF (TG_OP = 'INSERT') THEN
        -- Дополнительное логирование критичных действий
        -- Примечание: таблица moderatoraction отсутствует в схеме, поэтому этот триггер не будет работать
        -- Оставляем для совместимости, но он не будет выполняться
        IF NEW.action_type IN ('delete_post', 'delete_topic', 'block_user') THEN
            INSERT INTO system_logs (
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
                'moderator'::user_role_enum,
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
$$ LANGUAGE plpgsql;

-- Триггер для moderatoraction отключен, так как таблица отсутствует в схеме
-- DROP TRIGGER IF EXISTS trigger_audit_moderator_actions ON moderatoraction;
-- CREATE TRIGGER trigger_audit_moderator_actions
-- AFTER INSERT ON moderatoraction
-- FOR EACH ROW
-- EXECUTE FUNCTION audit_moderator_actions();

-- 7. Триггер валидации подписок
CREATE OR REPLACE FUNCTION validate_subscription()
RETURNS TRIGGER AS $$
BEGIN
    -- Проверяем, что пользователь не подписывается сам на себя
    IF NEW.subscriber_id = NEW.subscribed_to_id THEN
        RAISE EXCEPTION 'Пользователь не может подписаться сам на себя';
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Триггер для usersubscription отключен, так как таблица отсутствует в схеме
-- DROP TRIGGER IF EXISTS trigger_validate_subscription ON usersubscription;
-- CREATE TRIGGER trigger_validate_subscription
-- BEFORE INSERT OR UPDATE ON usersubscription
-- FOR EACH ROW
-- EXECUTE FUNCTION validate_subscription();

-- 8. Триггер начисления очков за достижения
CREATE OR REPLACE FUNCTION award_points_for_achievement()
RETURNS TRIGGER AS $$
BEGIN
    IF (TG_OP = 'INSERT') THEN
        -- Начисляем 10 очков за каждое достижение
        UPDATE user_rank_progress
        SET current_points = current_points + 10
        WHERE user_id = NEW.user_id;
        
        -- Логируем выдачу достижения
        INSERT INTO system_logs (
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
            'user'::user_role_enum,
            'Получено достижение #' || NEW.achievement_id,
            'achievement',
            NEW.achievement_id,
            CURRENT_TIMESTAMP
        );
        
        RETURN NEW;
    END IF;
    RETURN NULL;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trigger_award_points_for_achievement ON user_achievements;
CREATE TRIGGER trigger_award_points_for_achievement
AFTER INSERT ON user_achievements
FOR EACH ROW
EXECUTE FUNCTION award_points_for_achievement();
