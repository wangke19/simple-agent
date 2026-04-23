"""
进销存管理系统 - 数据库层
使用 SQLite 数据库
"""

import sqlite3
from datetime import datetime
from typing import List, Dict, Optional, Tuple


class Database:
    """数据库管理类"""
    
    def __init__(self, db_name: str = "inventory.db"):
        """初始化数据库连接"""
        self.db_name = db_name
        self.conn = None
        self.connect()
        self.create_tables()
    
    def connect(self):
        """连接数据库"""
        self.conn = sqlite3.connect(self.db_name)
        self.conn.row_factory = sqlite3.Row  # 返回字典形式的结果
    
    def close(self):
        """关闭数据库连接"""
        if self.conn:
            self.conn.close()
    
    def create_tables(self):
        """创建数据表"""
        cursor = self.conn.cursor()
        
        # 创建商品表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS products (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                category TEXT NOT NULL,
                unit TEXT NOT NULL,
                price REAL NOT NULL,
                stock INTEGER NOT NULL DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # 创建进货表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS purchases (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                product_id INTEGER NOT NULL,
                quantity INTEGER NOT NULL,
                unit_price REAL NOT NULL,
                total REAL NOT NULL,
                date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (product_id) REFERENCES products (id)
            )
        """)
        
        # 创建销售表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS sales (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                product_id INTEGER NOT NULL,
                quantity INTEGER NOT NULL,
                unit_price REAL NOT NULL,
                total REAL NOT NULL,
                date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (product_id) REFERENCES products (id)
            )
        """)
        
        self.conn.commit()
    
    # ==================== 商品管理 ====================
    
    def add_product(self, name: str, category: str, unit: str, price: float, stock: int = 0) -> int:
        """添加商品"""
        cursor = self.conn.cursor()
        cursor.execute("""
            INSERT INTO products (name, category, unit, price, stock)
            VALUES (?, ?, ?, ?, ?)
        """, (name, category, unit, price, stock))
        self.conn.commit()
        return cursor.lastrowid
    
    def get_product(self, product_id: int) -> Optional[Dict]:
        """获取单个商品"""
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM products WHERE id = ?", (product_id,))
        row = cursor.fetchone()
        return dict(row) if row else None
    
    def get_all_products(self) -> List[Dict]:
        """获取所有商品"""
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM products ORDER BY id")
        return [dict(row) for row in cursor.fetchall()]
    
    def search_products(self, keyword: str) -> List[Dict]:
        """搜索商品"""
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT * FROM products 
            WHERE name LIKE ? OR category LIKE ?
            ORDER BY id
        """, (f"%{keyword}%", f"%{keyword}%"))
        return [dict(row) for row in cursor.fetchall()]
    
    def update_product(self, product_id: int, name: str, category: str, unit: str, price: float, stock: int) -> bool:
        """更新商品信息"""
        cursor = self.conn.cursor()
        cursor.execute("""
            UPDATE products 
            SET name = ?, category = ?, unit = ?, price = ?, stock = ?
            WHERE id = ?
        """, (name, category, unit, price, stock, product_id))
        self.conn.commit()
        return cursor.rowcount > 0
    
    def delete_product(self, product_id: int) -> bool:
        """删除商品"""
        cursor = self.conn.cursor()
        cursor.execute("DELETE FROM products WHERE id = ?", (product_id,))
        self.conn.commit()
        return cursor.rowcount > 0
    
    def update_product_stock(self, product_id: int, quantity: int) -> bool:
        """更新商品库存"""
        cursor = self.conn.cursor()
        cursor.execute("""
            UPDATE products 
            SET stock = stock + ?
            WHERE id = ?
        """, (quantity, product_id))
        self.conn.commit()
        return cursor.rowcount > 0
    
    # ==================== 进货管理 ====================
    
    def add_purchase(self, product_id: int, quantity: int, unit_price: float, date: str = None) -> int:
        """添加进货记录"""
        if date is None:
            date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        total = quantity * unit_price
        
        cursor = self.conn.cursor()
        cursor.execute("""
            INSERT INTO purchases (product_id, quantity, unit_price, total, date)
            VALUES (?, ?, ?, ?, ?)
        """, (product_id, quantity, unit_price, total, date))
        
        # 更新商品库存
        self.update_product_stock(product_id, quantity)
        
        self.conn.commit()
        return cursor.lastrowid
    
    def get_purchase(self, purchase_id: int) -> Optional[Dict]:
        """获取单条进货记录"""
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT p.*, pr.name as product_name 
            FROM purchases p
            LEFT JOIN products pr ON p.product_id = pr.id
            WHERE p.id = ?
        """, (purchase_id,))
        row = cursor.fetchone()
        return dict(row) if row else None
    
    def get_all_purchases(self, limit: int = None) -> List[Dict]:
        """获取所有进货记录"""
        cursor = self.conn.cursor()
        if limit:
            cursor.execute("""
                SELECT p.*, pr.name as product_name 
                FROM purchases p
                LEFT JOIN products pr ON p.product_id = pr.id
                ORDER BY p.date DESC
                LIMIT ?
            """, (limit,))
        else:
            cursor.execute("""
                SELECT p.*, pr.name as product_name 
                FROM purchases p
                LEFT JOIN products pr ON p.product_id = pr.id
                ORDER BY p.date DESC
            """)
        return [dict(row) for row in cursor.fetchall()]
    
    def get_purchases_by_date(self, start_date: str, end_date: str) -> List[Dict]:
        """按日期范围查询进货记录"""
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT p.*, pr.name as product_name 
            FROM purchases p
            LEFT JOIN products pr ON p.product_id = pr.id
            WHERE p.date BETWEEN ? AND ?
            ORDER BY p.date DESC
        """, (start_date, end_date))
        return [dict(row) for row in cursor.fetchall()]
    
    # ==================== 销售管理 ====================
    
    def add_sale(self, product_id: int, quantity: int, unit_price: float, date: str = None) -> Optional[int]:
        """添加销售记录"""
        if date is None:
            date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # 检查库存是否足够
        product = self.get_product(product_id)
        if not product or product['stock'] < quantity:
            return None
        
        total = quantity * unit_price
        
        cursor = self.conn.cursor()
        cursor.execute("""
            INSERT INTO sales (product_id, quantity, unit_price, total, date)
            VALUES (?, ?, ?, ?, ?)
        """, (product_id, quantity, unit_price, total, date))
        
        # 扣减商品库存
        self.update_product_stock(product_id, -quantity)
        
        self.conn.commit()
        return cursor.lastrowid
    
    def get_sale(self, sale_id: int) -> Optional[Dict]:
        """获取单条销售记录"""
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT s.*, pr.name as product_name 
            FROM sales s
            LEFT JOIN products pr ON s.product_id = pr.id
            WHERE s.id = ?
        """, (sale_id,))
        row = cursor.fetchone()
        return dict(row) if row else None
    
    def get_all_sales(self, limit: int = None) -> List[Dict]:
        """获取所有销售记录"""
        cursor = self.conn.cursor()
        if limit:
            cursor.execute("""
                SELECT s.*, pr.name as product_name 
                FROM sales s
                LEFT JOIN products pr ON s.product_id = pr.id
                ORDER BY s.date DESC
                LIMIT ?
            """, (limit,))
        else:
            cursor.execute("""
                SELECT s.*, pr.name as product_name 
                FROM sales s
                LEFT JOIN products pr ON s.product_id = pr.id
                ORDER BY s.date DESC
            """)
        return [dict(row) for row in cursor.fetchall()]
    
    def get_sales_by_date(self, start_date: str, end_date: str) -> List[Dict]:
        """按日期范围查询销售记录"""
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT s.*, pr.name as product_name 
            FROM sales s
            LEFT JOIN products pr ON s.product_id = pr.id
            WHERE s.date BETWEEN ? AND ?
            ORDER BY s.date DESC
        """, (start_date, end_date))
        return [dict(row) for row in cursor.fetchall()]
    
    # ==================== 统计报表 ====================
    
    def get_stock_summary(self) -> List[Dict]:
        """获取库存汇总"""
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT id, name, category, unit, price, stock,
                   stock * price as total_value
            FROM products
            ORDER BY stock ASC
        """)
        return [dict(row) for row in cursor.fetchall()]
    
    def get_low_stock_products(self, threshold: int = 10) -> List[Dict]:
        """获取低库存商品"""
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT * FROM products
            WHERE stock <= ?
            ORDER BY stock ASC
        """, (threshold,))
        return [dict(row) for row in cursor.fetchall()]
    
    def get_purchase_summary(self) -> Dict:
        """获取进货汇总统计"""
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT 
                COUNT(*) as total_count,
                SUM(quantity) as total_quantity,
                SUM(total) as total_amount
            FROM purchases
        """)
        row = cursor.fetchone()
        return {
            'total_count': row[0] or 0,
            'total_quantity': row[1] or 0,
            'total_amount': row[2] or 0
        }
    
    def get_sales_summary(self) -> Dict:
        """获取销售汇总统计"""
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT 
                COUNT(*) as total_count,
                SUM(quantity) as total_quantity,
                SUM(total) as total_amount
            FROM sales
        """)
        row = cursor.fetchone()
        return {
            'total_count': row[0] or 0,
            'total_quantity': row[1] or 0,
            'total_amount': row[2] or 0
        }


# 创建全局数据库实例
db = Database()


if __name__ == "__main__":
    # 测试代码
    database = Database()
    
    # 添加测试商品
    database.add_product("笔记本电脑", "电子产品", "台", 4999.99, 50)
    database.add_product("无线鼠标", "电子产品", "个", 59.9, 200)
    database.add_product("机械键盘", "电子产品", "个", 299.0, 100)
    
    # 测试进货
    database.add_purchase(1, 10, 4800.0)
    
    # 测试销售
    database.add_sale(2, 5, 59.9)
    
    # 查询所有商品
    print("\n=== 所有商品 ===")
    for product in database.get_all_products():
        print(f"{product['id']}. {product['name']} - 库存: {product['stock']}")
    
    # 查询库存汇总
    print("\n=== 库存汇总 ===")
    for item in database.get_stock_summary():
        print(f"{item['name']}: {item['stock']} {item['unit']} - 价值: {item['total_value']:.2f}元")
    
    database.close()
