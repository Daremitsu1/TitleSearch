-- ========================================
-- procedures.sql
-- ========================================

DELIMITER $$

-- User sign-on procedure
CREATE DEFINER=`root`@`localhost` PROCEDURE `sp_user_sign_on`(
    IN p_username VARCHAR(50),
    IN p_email VARCHAR(100),
    IN p_password_hash VARCHAR(255)
)
BEGIN
    DECLARE v_user_exists INT;

    SELECT COUNT(*) INTO v_user_exists
    FROM user_sign_on
    WHERE username = p_username OR email = p_email;

    IF v_user_exists > 0 THEN
        SELECT 'ERROR: Username or Email already exists' AS message;
    ELSE
        INSERT INTO user_sign_on (username, email, password_hash)
        VALUES (p_username, p_email, p_password_hash);
        SELECT 'SUCCESS: User registered' AS message, LAST_INSERT_ID() AS user_id;
    END IF;
END $$

-- User login procedure
CREATE DEFINER=`root`@`localhost` PROCEDURE `sp_user_login`(
    IN p_username VARCHAR(50),
    IN p_password_hash VARCHAR(255),
    IN p_ip_address VARCHAR(45)
)
BEGIN
    DECLARE v_user_id INT;
    DECLARE v_success BOOLEAN;

    SELECT user_id INTO v_user_id
    FROM user_sign_on
    WHERE username = p_username AND password_hash = p_password_hash;

    SET v_success = (v_user_id IS NOT NULL);

    IF v_success THEN
        INSERT INTO user_login (user_id, ip_address, success)
        VALUES (v_user_id, p_ip_address, TRUE);
        SELECT 'SUCCESS: Login successful' AS message, v_user_id AS user_id;
    ELSE
        SELECT user_id INTO v_user_id
        FROM user_sign_on
        WHERE username = p_username;

        IF v_user_id IS NOT NULL THEN
            INSERT INTO user_login (user_id, ip_address, success)
            VALUES (v_user_id, p_ip_address, FALSE);
        END IF;

        SELECT 'ERROR: Invalid username or password' AS message;
    END IF;
END $$

-- Insert job
CREATE DEFINER=`root`@`localhost` PROCEDURE `sp_insert_job`(
    IN p_user_id INT,
    IN p_state_id INT,
    IN p_county_id INT,
    IN p_website_id INT,
    IN p_job_name VARCHAR(255),
    OUT p_job_id INT
)
BEGIN
    INSERT INTO job_list (user_id, state_id, county_id, website_id, job_name, created_at, updated_at)
    VALUES (p_user_id, p_state_id, p_county_id, p_website_id, p_job_name, NOW(), NOW());

    SET p_job_id = LAST_INSERT_ID();
END $$

-- Insert document
CREATE DEFINER=`root`@`localhost` PROCEDURE `sp_insert_document`(
    IN p_job_id INT,
    IN p_doc_name VARCHAR(255)
)
BEGIN
    INSERT INTO document_list (job_id, doc_name)
    VALUES (p_job_id, p_doc_name);

    SELECT LAST_INSERT_ID() AS doc_id;
END $$

-- Get all states
CREATE DEFINER=`root`@`localhost` PROCEDURE `sp_get_states`()
BEGIN
    SELECT state_id, state_name, state_code
    FROM state_list
    ORDER BY state_name;
END $$

-- Get counties by state
CREATE DEFINER=`root`@`localhost` PROCEDURE `sp_get_counties_by_state`(
    IN p_state_id INT
)
BEGIN
    SELECT county_id, county_name, fips_code
    FROM county_list
    WHERE state_id = p_state_id
    ORDER BY county_name;
END $$

-- Get websites by state and county
CREATE DEFINER=`root`@`localhost` PROCEDURE `sp_get_websites_by_state_county`(
    IN p_state_id INT,
    IN p_county_id INT
)
BEGIN
    SELECT w.website_id, w.website_name, w.serial_code
    FROM website_list w
    INNER JOIN county_list c 
        ON w.county_id = c.county_id
    WHERE c.state_id = p_state_id
      AND w.county_id = p_county_id
    ORDER BY w.website_name;
END $$

-- Get status ID by status name
CREATE DEFINER=`root`@`localhost` PROCEDURE `sp_get_status_id`(
    IN p_status_name VARCHAR(50)
)
BEGIN
    SELECT status_id
    FROM status_db
    WHERE status_name = p_status_name;
END $$

DELIMITER ;
