import psycopg2
from psycopg2 import pool
from psycopg2.extras import RealDictCursor
import streamlit as st

@st.cache_resource
def get_connection_pool():
    """
    تهيئة بركة الاتصال (Connection Pool) باستخدام رابط الاتصال الموحد (Connection String)
    من ملف secrets.toml الخاص بـ Streamlit.
    """
    try:
        # قراءة رابط الاتصال الموحد
        db_url = st.secrets["DATABASE_URL"]
    except FileNotFoundError:
        st.error("🚨 ملف `secrets.toml` غير موجود! تأكد من إنشائه داخل مجلد `.streamlit`.")
        st.stop()
    except KeyError:
        st.error("🚨 المتغير `DATABASE_URL` غير موجود داخل ملف `secrets.toml`.")
        st.stop()

    # استخدام الـ dsn (Data Source Name) لفتح الاتصال بالرابط الموحد مباشرة
    return pool.SimpleConnectionPool(
        1, 20,
        dsn=db_url
    )

# تعريف الـ pool مرة واحدة
db_pool = get_connection_pool()

def fetch_query(query, params=None):
    """تنفيذ الاستعلامات المتعددة مع حماية ذكية للاتصال."""
    conn = None
    try:
        conn = db_pool.getconn()
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(query, params)
            results = cur.fetchall()
        db_pool.putconn(conn)
        return results
    except (psycopg2.OperationalError, psycopg2.InterfaceError):
        # في حالة موت الاتصال، يتم التخلص منه وسحب واحد جديد
        if conn:
            db_pool.putconn(conn, close=True)
            conn = None
        try:
            conn = db_pool.getconn()
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(query, params)
                results = cur.fetchall()
            db_pool.putconn(conn)
            return results
        except Exception as retry_err:
            if conn:
                db_pool.putconn(conn, close=True)
            st.error(f"فشل الاتصال بقاعدة البيانات بعد إعادة المحاولة: {retry_err}")
            return None
    except Exception as e:
        st.error(f"خطأ غير متوقع: {e}")
        if conn:
            try:
                conn.rollback()
            except:
                pass
            db_pool.putconn(conn)
        return None

def fetch_one(query, params=None):
    """تنفيذ استعلام لصف واحد (مثل تسجيل الدخول) مع حماية ذكية للاتصال."""
    conn = None
    try:
        conn = db_pool.getconn()
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(query, params)
            result = cur.fetchone()
        db_pool.putconn(conn)
        return result
    except (psycopg2.OperationalError, psycopg2.InterfaceError):
        # في حالة موت الاتصال، يتم التخلص منه وسحب واحد جديد
        if conn:
            db_pool.putconn(conn, close=True)
            conn = None
        try:
            conn = db_pool.getconn()
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(query, params)
                result = cur.fetchone()
            db_pool.putconn(conn)
            return result
        except Exception as retry_err:
            if conn:
                db_pool.putconn(conn, close=True)
            st.error(f"فشل الاتصال بقاعدة البيانات بعد إعادة المحاولة: {retry_err}")
            return None
    except Exception as e:
        st.error(f"خطأ غير متوقع: {e}")
        if conn:
            try:
                conn.rollback()
            except:
                pass
            db_pool.putconn(conn)
        return None