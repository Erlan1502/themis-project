import sqlite3
import json

conn = sqlite3.connect('themis_data.db')
c = conn.cursor()

c.execute("SELECT extraction_json, total_tokens, turns_count, in_class_grade, ai_depth_score FROM student_audits WHERE student_id = 'stud_aai_042'")
row = c.fetchone()
ext = json.loads(row[0])
print("=== EXTRACTION JSON ===")
print(json.dumps(ext, indent=2, ensure_ascii=False))
print(f"total_tokens = {row[1]}, turns_count = {row[2]}, in_class_grade = {row[3]}, ai_depth_score = {row[4]}")

print("\n=== ALL TURNS FOR THIS SESSION ===")
c.execute("SELECT turn_number, student_message, system_reply, paste_detected, similarity_score FROM dialog_turns WHERE student_message != '' ORDER BY turn_number")
for t in c.fetchall():
    print(f"\n--- Turn {t[0]} (paste={t[3]}, sim={t[4]}) ---")
    print("STUDENT:", t[1])
    print("SYSTEM:", t[2][:120], "...")
