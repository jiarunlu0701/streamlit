from db import db
class count:
    def update_token_usage(self, prompt_tokens, completion_tokens, total_tokens):
        conn = db.get_db_connection()
        conn.execute('INSERT INTO TOKEN_USAGE (prompt_tokens, completion_tokens, total_tokens) VALUES (?, ?, ?)',
                     (prompt_tokens, completion_tokens, total_tokens))
        conn.commit()
        conn.close()

    def get_latest_token_usage(self):
        conn = db.get_db_connection()
        token_usage = conn.execute('SELECT * FROM TOKEN_USAGE ORDER BY id DESC LIMIT 1').fetchone()
        conn.close()
        return token_usage if token_usage else None
    def reset_token_usage(self):
        conn = db.get_db_connection()
        conn.execute('DELETE FROM TOKEN_USAGE')  # Assuming TOKEN_USAGE is your table name
        conn.commit()
        conn.close()

    def count_tokens(self, text):
        return len(text.split())