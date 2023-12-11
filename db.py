import sqlite3
class db:
    def get_db_connection(self):
        conn = sqlite3.connect('assets/chat_history.db')
        conn.row_factory = sqlite3.Row
        return conn

    def get_chat_history_descending(self):
        conn = self.get_db_connection()
        # Fetch entries in descending order so the newest are first
        chats = conn.execute(
            "SELECT * FROM CHAT WHERE ROLE IN ('User', 'SAP Digital School AI') ORDER BY ID DESC").fetchall()
        conn.close()
        return chats

    def get_last_two_chats(self):
        conn = self.get_db_connection()
        # Fetch the last two entries
        last_two_chats = conn.execute(
            "SELECT * FROM CHAT WHERE ROLE IN ('User', 'SAP Digital School AI') ORDER BY ID DESC LIMIT 2").fetchall()
        conn.close()
        return last_two_chats

    def add_chat(self, role, message, image_urls=None):
        conn = self.get_db_connection()
        if image_urls:
            image_urls_str = ','.join(image_urls)  # Joining the URLs into a single string
            conn.execute('INSERT INTO CHAT (ROLE, MESSAGE, IMAGE_URL) VALUES (?, ?, ?)',
                         (role, message, image_urls_str))
        else:
            conn.execute('INSERT INTO CHAT (ROLE, MESSAGE) VALUES (?, ?)', (role, message))
        conn.commit()
        conn.close()

    def delete_chat_history(self):
        conn = self.get_db_connection()
        conn.execute('DELETE FROM CHAT')
        conn.commit()
        conn.close()

    def save_prompt(self, prompt_text):
        conn = self.get_db_connection()
        conn.execute('INSERT INTO PROMPTS (prompt) VALUES (?)', (prompt_text,))
        conn.commit()
        conn.close()

    def get_latest_prompt(self):
        conn = self.get_db_connection()
        prompt = conn.execute('SELECT prompt FROM PROMPTS ORDER BY id DESC LIMIT 1').fetchone()
        conn.close()
        return prompt['prompt'] if prompt else None