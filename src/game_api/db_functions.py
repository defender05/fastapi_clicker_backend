# ШАБЛОН - Запуск каждую минуту
# SELECT cron.schedule('* * * * *', 'SELECT function_name()');

# CREATE EXTENSION pg_cron;

# вызов каждый час
# SELECT cron.schedule('0 * * * *', 'SELECT update_game_balance()');
# SELECT cron.schedule('0 * * * *', 'SELECT update_country_ratings()');

# вызов каждые 24 часа
# SELECT cron.schedule('0 0 * * *', 'SELECT recharge_user_energy()');
# SELECT cron.schedule('0 0 * * *', 'SELECT calculate_and_append_referral_commissions()');




# восстановление энергии юзера
# вызывается раз в 24 часа
recharge_user_energy = """
BEGIN
    UPDATE users
    SET energy = 500;
END
"""

# обновление рейтинга по странам
# вызывается каждый час
update_country_ratings = """
BEGIN
    DELETE FROM country_ratings;
    INSERT INTO country_ratings
    SELECT
        countries.id AS country_id,
        COUNT(users.id) AS user_count,
        SUM(users.game_balance) AS total_balance
    FROM
        users
    JOIN
        countries ON users.country_id = countries.id
    GROUP BY
        countries.id;
END;
"""

# начисление игровой валюты в размере текущей производительности пользователя
# вызывается каждый час
update_game_balance = """
BEGIN
    UPDATE users
    SET game_balance = game_balance + total_capacity;
END;
"""

# начисление процента заработанной валюты от рефералов пользователю
# вызывается каждые 24 часа
calculate_and_append_referral_commissions = """
DECLARE
    user_record RECORD;
    referral_record RECORD;
    commission_rate FLOAT;
    earned_currency FLOAT;
    commission_amount FLOAT;
BEGIN
    FOR user_record IN SELECT * FROM users LOOP
        FOR referral_record IN SELECT * FROM user_referrals WHERE owner_id = user_record.id LOOP
            SELECT commision_rate INTO commission_rate FROM referral_levels WHERE id = referral_record.level_id;
            -- Получаем заработанную валюту рефералов
            SELECT game_balance INTO earned_currency FROM users WHERE id = referral_record.referral_id;
            -- Вычисляем итоговое кол-во начисляемой валюты
            commission_amount := earned_currency * commission_rate;
            -- Начисляем комиссионные пользователю
            UPDATE users SET game_balance = game_balance + commission_amount WHERE id = user_record.id;
        END LOOP;
    END LOOP;
END;
"""