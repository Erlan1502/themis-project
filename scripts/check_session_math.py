import sqlite3

conn = sqlite3.connect('themis_data.db')
c = conn.cursor()

c.execute("SELECT student_id, in_class_grade, turns_count, total_tokens, ai_depth_score, raw_delta, rectified_delta, z_score, zone, session_status, extraction_json FROM student_audits WHERE student_id in ('stud_aai_042', 'stud_01') or ai_depth_score between 73.0 and 74.5")
for r in c.fetchall():
    print('AUDIT:', r[:10])
    if r[10]:
        print('  EXTRACTION:', r[10][:250])

print("\n--- SESSIONS ---")
c.execute("SELECT session_id, student_id, turns_count, active, created_at FROM sessions ORDER BY created_at DESC LIMIT 10")
for r in c.fetchall():
    print(r)

print("\n--- DIALOG TURNS ---")
c.execute("SELECT session_id, turn_number, student_message, paste_detected FROM dialog_turns ORDER BY id DESC LIMIT 15")
for r in c.fetchall():
    print(f"Turn {r[1]} (paste={r[3]}): {r[2][:80]}...")
