# Rate Limiting Implementation for Login Attempts

## Overview

This implementation adds rate limiting to prevent brute force attacks on user login attempts. If a user tries to login 5 times in a minute with incorrect credentials, their account will be blocked for 30 minutes.

## Features

- **Failed Attempt Tracking**: All login attempts (successful and failed) are logged in the database
- **Rate Limiting**: Users are blocked after 5 failed attempts within 1 minute
- **Temporary Blocking**: Blocked users must wait 30 minutes before attempting to login again
- **IP Address Logging**: Login attempts include IP address for security monitoring
- **Cross-Endpoint Protection**: Both `/login` and `/token` endpoints are protected
- **User-Specific Limits**: Each user has independent rate limits

## Database Schema

A new table `login_attempts` was added to track all login attempts:

```sql
CREATE TABLE login_attempts (
    id INTEGER PRIMARY KEY,
    username TEXT NOT NULL,
    ip_address TEXT,
    success INTEGER DEFAULT 0,  -- 0 = failed, 1 = success
    timestamp DATETIME NOT NULL
);
```

## Implementation Details

### Core Functions

1. **`log_login_attempt(db, username, ip_address, success)`**
   - Logs every login attempt to the database
   - Records username, IP address, success status, and timestamp

2. **`is_user_blocked(db, username)`**
   - Checks if a user is currently blocked
   - Returns `True` if user has 5+ failed attempts in the last minute AND is still within 30-minute block period

3. **`get_block_remaining_time(db, username)`**
   - Calculates remaining block time in seconds
   - Returns 0 if user is not blocked

### Rate Limiting Logic

1. **Detection**: 5 failed login attempts within 1 minute triggers blocking
2. **Block Duration**: 30 minutes from the time of the 5th failed attempt
3. **Block Scope**: Affects both `/login` and `/token` endpoints
4. **Reset**: Block automatically expires after 30 minutes

### Login Endpoint Changes

Both `/login` and `/token` endpoints now:

1. Check if user is blocked before processing credentials
2. Return HTTP 429 (Too Many Requests) if blocked
3. Log all login attempts (success and failure)
4. Include IP address in logs for security monitoring

## HTTP Response Codes

- **200**: Successful login
- **401**: Invalid credentials (username/password incorrect)
- **429**: Rate limited (too many failed attempts)
- **500**: Server error

## Error Messages

- **Invalid credentials**: "Incorrect username or password"
- **Rate limited**: "Account temporarily blocked due to too many failed login attempts. Please try again in X minutes and Y seconds."

## Security Considerations

### What This Protects Against

- **Brute Force Attacks**: Prevents automated password guessing
- **Dictionary Attacks**: Limits attempts to try common passwords
- **Credential Stuffing**: Stops attackers from testing leaked credentials

### What This Doesn't Protect Against

- **Distributed Attacks**: Multiple IP addresses can still attack the same user
- **Account Enumeration**: Attackers can still discover valid usernames
- **Password Spraying**: Attackers can try one password against many users

### Additional Security Recommendations

1. **IP-Based Rate Limiting**: Consider adding IP-based limits in addition to user-based limits
2. **Account Lockout Notifications**: Send email alerts when accounts are locked
3. **CAPTCHA Integration**: Add CAPTCHA after first few failed attempts
4. **Geolocation Monitoring**: Track unusual login locations
5. **Multi-Factor Authentication**: Require 2FA for sensitive accounts

## Testing

### Unit Tests

Run the comprehensive unit tests:

```bash
python -m pytest test_rate_limiting.py -v
```

Test categories:
- Login attempt logging
- User blocking logic
- Block time calculation
- Login endpoint protection
- Token endpoint protection
- Integration tests

### Manual Testing

Run the manual test script:

```bash
python manual_test_rate_limiting.py
```

This script tests:
- Successful login
- Failed login
- Rate limiting after 5 attempts
- Blocked user with correct password
- Token endpoint rate limiting
- Database logging

## Configuration

The rate limiting parameters are currently hardcoded but can be made configurable:

```python
# Current hardcoded values
FAILED_ATTEMPTS_THRESHOLD = 5      # Number of failed attempts before blocking
ATTEMPT_WINDOW_MINUTES = 1         # Time window for counting attempts
BLOCK_DURATION_MINUTES = 30        # How long to block the user
```

## Monitoring and Maintenance

### Database Maintenance

Consider adding a cleanup job to remove old login attempts:

```sql
DELETE FROM login_attempts 
WHERE timestamp < NOW() - INTERVAL '30 days';
```

### Monitoring Queries

Track suspicious activity:

```sql
-- Users with multiple failed attempts
SELECT username, COUNT(*) as failed_attempts 
FROM login_attempts 
WHERE success = 0 AND timestamp > NOW() - INTERVAL '1 hour'
GROUP BY username 
ORDER BY failed_attempts DESC;

-- Most common attack IP addresses
SELECT ip_address, COUNT(*) as attempts 
FROM login_attempts 
WHERE success = 0 AND timestamp > NOW() - INTERVAL '1 day'
GROUP BY ip_address 
ORDER BY attempts DESC;
```

## Performance Considerations

- **Database Indexing**: Ensure indexes on `username` and `timestamp` columns
- **Query Optimization**: Consider caching blocked users in memory
- **Database Growth**: Implement log rotation to prevent unbounded growth
- **Connection Pooling**: Use connection pooling for high-traffic applications

## Future Enhancements

1. **Configurable Limits**: Make thresholds configurable via environment variables
2. **Admin Override**: Allow administrators to manually unblock users
3. **Whitelist IPs**: Allow certain IP addresses to bypass rate limiting
4. **Progressive Delays**: Increase delay time with each failed attempt
5. **Account Recovery**: Provide secure account recovery options for blocked users