"""
数据库操作模块
提供销售记录和商品的查询功能
"""

# ============ 商品管理功能 ============

def get_products(keyword=None, category=None, status=None):
    """
    查询商品列表
    
    Args:
        keyword (str, optional): 搜索关键词（商品名称或ID）
        category (str, optional): 商品分类筛选
        status (str, optional): 商品状态筛选（在售/缺货/下架）
    
    Returns:
        list: 商品列表，每条商品包含：
            - id: 商品ID
            - name: 商品名称
            - category: 商品分类
            - price: 价格
            - stock: 库存数量
            - status: 商品状态
    """
    sample_products = [
        {'id': 'P001', 'name': '笔记本电脑', 'category': '电子产品', 'price': 5999.00, 'stock': 50, 'status': '在售'},
        {'id': 'P002', 'name': '无线鼠标', 'category': '电子产品', 'price': 99.00, 'stock': 200, 'status': '在售'},
        {'id': 'P003', 'name': '办公椅', 'category': '办公用品', 'price': 399.00, 'stock': 30, 'status': '在售'},
        {'id': 'P004', 'name': '签字笔', 'category': '办公用品', 'price': 5.00, 'stock': 500, 'status': '在售'},
        {'id': 'P005', 'name': '保温杯', 'category': '日用品', 'price': 59.00, 'stock': 0, 'status': '缺货'},
        {'id': 'P006', 'name': '机械键盘', 'category': '电子产品', 'price': 299.00, 'stock': 80, 'status': '在售'},
        {'id': 'P007', 'name': '显示器', 'category': '电子产品', 'price': 1299.00, 'stock': 25, 'status': '在售'},
        {'id': 'P008', 'name': '文件夹', 'category': '办公用品', 'price': 8.00, 'stock': 300, 'status': '在售'},
    ]
    
    result = sample_products
    
    # 关键词筛选
    if keyword:
        result = [p for p in result if keyword.lower() in p['name'].lower() or keyword.lower() in p['id'].lower()]
    
    # 分类筛选
    if category:
        result = [p for p in result if p['category'] == category]
    
    # 状态筛选
    if status:
        result = [p for p in result if p['status'] == status]
    
    return result


def get_product_by_id(product_id):
    """
    根据ID获取单个商品
    
    Args:
        product_id (str): 商品ID
    
    Returns:
        dict: 商品信息，不存在返回None
    """
    products = get_products()
    for product in products:
        if product['id'] == product_id:
            return product
    return None


def add_product(product_data):
    """
    添加新商品
    
    Args:
        product_data (dict): 商品数据
            - id: 商品ID
            - name: 商品名称
            - category: 商品分类
            - price: 价格
            - stock: 库存数量
            - status: 商品状态
    
    Returns:
        bool: 添加成功返回True，失败返回False
    """
    # TODO: 实现真实的数据库插入操作
    print(f"[DB] 添加商品: {product_data}")
    return True


def update_product(product_id, product_data):
    """
    更新商品信息
    
    Args:
        product_id (str): 商品ID
        product_data (dict): 更新的商品数据
    
    Returns:
        bool: 更新成功返回True，失败返回False
    """
    # TODO: 实现真实的数据库更新操作
    print(f"[DB] 更新商品 {product_id}: {product_data}")
    return True


def delete_product(product_id):
    """
    删除商品
    
    Args:
        product_id (str): 商品ID
    
    Returns:
        bool: 删除成功返回True，失败返回False
    """
    # TODO: 实现真实的数据库删除操作
    print(f"[DB] 删除商品: {product_id}")
    return True


def get_categories():
    """
    获取所有商品分类
    
    Returns:
        list: 分类列表
    """
    products = get_products()
    categories = sorted(set(p['category'] for p in products))
    return categories


# ============ 销售记录功能 ============

def get_sales(start_date=None, end_date=None, limit=None):
    """
    查询销售记录
    
    Args:
        start_date (str, optional): 起始日期，格式 'YYYY-MM-DD'
        end_date (str, optional): 结束日期，格式 'YYYY-MM-DD'
        limit (int, optional): 返回记录的最大数量
    
    Returns:
        list: 销售记录列表，每条记录包含：
            - id: 销售ID
            - product_id: 产品ID
            - quantity: 销售数量
            - price: 单价
            - total: 总金额
            - sale_date: 销售日期
            - customer_name: 客户名称
    
    Example:
        >>> # 查询所有销售记录
        >>> sales = get_sales()
        >>> 
        >>> # 按日期范围查询
        >>> sales = get_sales(start_date='2024-01-01', end_date='2024-01-31')
        >>> 
        >>> # 限制返回数量
        >>> sales = get_sales(limit=10)
    """
    # TODO: 实现数据库查询逻辑
    # 这里提供示例数据，实际使用时需要连接真实数据库
    
    sample_sales = [
        {
            'id': 1,
            'product_id': 101,
            'quantity': 2,
            'price': 99.99,
            'total': 199.98,
            'sale_date': '2024-01-15',
            'customer_name': '张三'
        },
        {
            'id': 2,
            'product_id': 102,
            'quantity': 1,
            'price': 299.00,
            'total': 299.00,
            'sale_date': '2024-01-16',
            'customer_name': '李四'
        },
        {
            'id': 3,
            'product_id': 103,
            'quantity': 5,
            'price': 49.50,
            'total': 247.50,
            'sale_date': '2024-01-17',
            'customer_name': '王五'
        }
    ]
    
    # 应用日期过滤
    result = sample_sales
    
    if start_date:
        result = [s for s in result if s['sale_date'] >= start_date]
    
    if end_date:
        result = [s for s in result if s['sale_date'] <= end_date]
    
    # 应用限制数量
    if limit:
        result = result[:limit]
    
    return result
