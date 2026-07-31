import psycopg2
from psycopg2 import pool
from psycopg2.extras import RealDictCursor
import streamlit as st
import os

@st.cache_resource
def get_connection_pool():
    """
    تهيئة بركة الاتصال (Connection Pool) باستخدام رابط الاتصال الموحد (Connection String)
    سواء من متغيرات البيئة (في ديجيتال أوشن) أو من ملف secrets.toml (محلياً).
    """
    # 1. السيرفر هيحاول يقرأ الرابط من إعدادات ديجيتال أوشن
    db_url = os.getenv("DATABASE_URL")
    
    # 2. لو ملقاهوش (يعني إنت شغال على اللاب توب بتاعك)، هيقرأ من ملف secrets
    if not db_url:
        try:
            db_url = st.secrets["DATABASE_URL"]
        except FileNotFoundError:
            st.error("🚨 ملف `secrets.toml` غير موجود، ولم يتم العثور على المتغير في بيئة التشغيل.")
            st.stop()
        except KeyError:
            st.error("🚨 المتغير `DATABASE_URL` غير موجود.")
            st.stop()

    # استخدام الـ dsn لفتح الاتصال بالرابط الموحد مباشرة
    return pool.SimpleConnectionPool(
        1, 20,
        dsn=db_url
    )

def fetch_query(query, params=None):
    """تنفيذ الاستعلامات المتعددة مع حماية ذكية ومسح للكاش عند انقطاع الاتصال."""
    # بننادي على الدالة هنا عشان دايماً تجيب أحدث نسخة من الكاش
    db_pool = get_connection_pool()
    conn = None
    try:
        conn = db_pool.getconn()
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(query, params)
            results = cur.fetchall()
        db_pool.putconn(conn)
        return results
        
    except (psycopg2.OperationalError, psycopg2.InterfaceError):
        # ⚠️ الاتصال مات! البركة كلها غالباً مسمومة
        if conn:
            db_pool.putconn(conn, close=True)
            
        # 💡 السحر هنا: فجّر الكاش وابني بركة اتصالات جديدة من الصفر
        st.cache_resource.clear()
        fresh_pool = get_connection_pool()
        
        try:
            conn = fresh_pool.getconn()
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(query, params)
                results = cur.fetchall()
            fresh_pool.putconn(conn)
            return results
        except Exception as retry_err:
            if conn:
                fresh_pool.putconn(conn, close=True)
            st.error(f"فشل الاتصال بقاعدة البيانات حتى بعد إعادة التنشيط: {retry_err}")
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
    """تنفيذ استعلام لصف واحد (مثل تسجيل الدخول) مع مسح للكاش عند انقطاع الاتصال."""
    db_pool = get_connection_pool()
    conn = None
    try:
        conn = db_pool.getconn()
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(query, params)
            result = cur.fetchone()
        db_pool.putconn(conn)
        return result
        
    except (psycopg2.OperationalError, psycopg2.InterfaceError):
        if conn:
            db_pool.putconn(conn, close=True)
            
        # مسح الكاش وبناء بركة جديدة لتسجيل الدخول
        st.cache_resource.clear()
        fresh_pool = get_connection_pool()
        
        try:
            conn = fresh_pool.getconn()
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(query, params)
                result = cur.fetchone()
            fresh_pool.putconn(conn)
            return result
        except Exception as retry_err:
            if conn:
                fresh_pool.putconn(conn, close=True)
            st.error(f"فشل الاتصال بقاعدة البيانات حتى بعد إعادة التنشيط: {retry_err}")
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