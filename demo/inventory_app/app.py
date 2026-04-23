import tkinter as tk
from tkinter import ttk, messagebox
from db import Database

class InventoryApp:
    def __init__(self, root):
        self.root = root
        self.root.title("进销存管理系统")
        self.root.geometry("900x600")
        
        self.db = Database()
        self.db.connect()
        
        self.create_widgets()
        self.refresh_products()
        self.refresh_purchases()
        self.refresh_sales()
        self.refresh_inventory()
        
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
    
    def create_widgets(self):
        notebook = ttk.Notebook(self.root)
        notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        self.create_product_tab(notebook)
        self.create_purchase_tab(notebook)
        self.create_sales_tab(notebook)
        self.create_inventory_tab(notebook)
    
    def create_product_tab(self, notebook):
        frame = ttk.Frame(notebook)
        notebook.add(frame, text="商品管理")
        
        input_frame = ttk.LabelFrame(frame, text="商品信息")
        input_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Label(input_frame, text="商品名称:").grid(row=0, column=0, padx=5, pady=5, sticky=tk.W)
        self.product_name = ttk.Entry(input_frame)
        self.product_name.grid(row=0, column=1, padx=5, pady=5)
        
        ttk.Label(input_frame, text="分类:").grid(row=0, column=2, padx=5, pady=5, sticky=tk.W)
        self.product_category = ttk.Entry(input_frame)
        self.product_category.grid(row=0, column=3, padx=5, pady=5)
        
        ttk.Label(input_frame, text="价格:").grid(row=1, column=0, padx=5, pady=5, sticky=tk.W)
        self.product_price = ttk.Entry(input_frame)
        self.product_price.grid(row=1, column=1, padx=5, pady=5)
        
        ttk.Label(input_frame, text="库存:").grid(row=1, column=2, padx=5, pady=5, sticky=tk.W)
        self.product_stock = ttk.Entry(input_frame)
        self.product_stock.grid(row=1, column=3, padx=5, pady=5)
        
        button_frame = ttk.Frame(input_frame)
        button_frame.grid(row=2, column=0, columnspan=4, pady=10)
        
        ttk.Button(button_frame, text="添加", command=self.add_product).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="更新", command=self.update_product).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="删除", command=self.delete_product).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="清空", command=self.clear_product_inputs).pack(side=tk.LEFT, padx=5)
        
        tree_frame = ttk.Frame(frame)
        tree_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        columns = ("id", "name", "category", "price", "stock")
        self.product_tree = ttk.Treeview(tree_frame, columns=columns, show="headings", selectmode="browse")
        
        self.product_tree.heading("id", text="ID")
        self.product_tree.heading("name", text="商品名称")
        self.product_tree.heading("category", text="分类")
        self.product_tree.heading("price", text="价格")
        self.product_tree.heading("stock", text="库存")
        
        self.product_tree.column("id", width=50)
        self.product_tree.column("name", width=150)
        self.product_tree.column("category", width=100)
        self.product_tree.column("price", width=80)
        self.product_tree.column("stock", width=80)
        
        scrollbar = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL, command=self.product_tree.yview)
        self.product_tree.configure(yscrollcommand=scrollbar.set)
        
        self.product_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.product_tree.bind("<<TreeviewSelect>>", self.on_product_select)
    
    def create_purchase_tab(self, notebook):
        frame = ttk.Frame(notebook)
        notebook.add(frame, text="进货登记")
        
        input_frame = ttk.LabelFrame(frame, text="进货信息")
        input_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Label(input_frame, text="商品ID:").grid(row=0, column=0, padx=5, pady=5, sticky=tk.W)
        self.purchase_product_id = ttk.Entry(input_frame)
        self.purchase_product_id.grid(row=0, column=1, padx=5, pady=5)
        
        ttk.Label(input_frame, text="数量:").grid(row=0, column=2, padx=5, pady=5, sticky=tk.W)
        self.purchase_quantity = ttk.Entry(input_frame)
        self.purchase_quantity.grid(row=0, column=3, padx=5, pady=5)
        
        ttk.Label(input_frame, text="进价:").grid(row=1, column=0, padx=5, pady=5, sticky=tk.W)
        self.purchase_price = ttk.Entry(input_frame)
        self.purchase_price.grid(row=1, column=1, padx=5, pady=5)
        
        ttk.Label(input_frame, text="供应商:").grid(row=1, column=2, padx=5, pady=5, sticky=tk.W)
        self.purchase_supplier = ttk.Entry(input_frame)
        self.purchase_supplier.grid(row=1, column=3, padx=5, pady=5)
        
        button_frame = ttk.Frame(input_frame)
        button_frame.grid(row=2, column=0, columnspan=4, pady=10)
        
        ttk.Button(button_frame, text="登记进货", command=self.register_purchase).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="清空", command=self.clear_purchase_inputs).pack(side=tk.LEFT, padx=5)
        
        tree_frame = ttk.Frame(frame)
        tree_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        columns = ("id", "product_id", "product_name", "quantity", "price", "supplier", "date")
        self.purchase_tree = ttk.Treeview(tree_frame, columns=columns, show="headings")
        
        self.purchase_tree.heading("id", text="ID")
        self.purchase_tree.heading("product_id", text="商品ID")
        self.purchase_tree.heading("product_name", text="商品名称")
        self.purchase_tree.heading("quantity", text="数量")
        self.purchase_tree.heading("price", text="进价")
        self.purchase_tree.heading("supplier", text="供应商")
        self.purchase_tree.heading("date", text="日期")
        
        scrollbar = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL, command=self.purchase_tree.yview)
        self.purchase_tree.configure(yscrollcommand=scrollbar.set)
        
        self.purchase_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
    
    def create_sales_tab(self, notebook):
        frame = ttk.Frame(notebook)
        notebook.add(frame, text="销售登记")
        
        input_frame = ttk.LabelFrame(frame, text="销售信息")
        input_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Label(input_frame, text="商品ID:").grid(row=0, column=0, padx=5, pady=5, sticky=tk.W)
        self.sales_product_id = ttk.Entry(input_frame)
        self.sales_product_id.grid(row=0, column=1, padx=5, pady=5)
        
        ttk.Label(input_frame, text="数量:").grid(row=0, column=2, padx=5, pady=5, sticky=tk.W)
        self.sales_quantity = ttk.Entry(input_frame)
        self.sales_quantity.grid(row=0, column=3, padx=5, pady=5)
        
        ttk.Label(input_frame, text="售价:").grid(row=1, column=0, padx=5, pady=5, sticky=tk.W)
        self.sales_price = ttk.Entry(input_frame)
        self.sales_price.grid(row=1, column=1, padx=5, pady=5)
        
        ttk.Label(input_frame, text="客户:").grid(row=1, column=2, padx=5, pady=5, sticky=tk.W)
        self.sales_customer = ttk.Entry(input_frame)
        self.sales_customer.grid(row=1, column=3, padx=5, pady=5)
        
        button_frame = ttk.Frame(input_frame)
        button_frame.grid(row=2, column=0, columnspan=4, pady=10)
        
        ttk.Button(button_frame, text="登记销售", command=self.register_sale).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="清空", command=self.clear_sales_inputs).pack(side=tk.LEFT, padx=5)
        
        tree_frame = ttk.Frame(frame)
        tree_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        columns = ("id", "product_id", "product_name", "quantity", "price", "customer", "date")
        self.sales_tree = ttk.Treeview(tree_frame, columns=columns, show="headings")
        
        self.sales_tree.heading("id", text="ID")
        self.sales_tree.heading("product_id", text="商品ID")
        self.sales_tree.heading("product_name", text="商品名称")
        self.sales_tree.heading("quantity", text="数量")
        self.sales_tree.heading("price", text="售价")
        self.sales_tree.heading("customer", text="客户")
        self.sales_tree.heading("date", text="日期")
        
        scrollbar = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL, command=self.sales_tree.yview)
        self.sales_tree.configure(yscrollcommand=scrollbar.set)
        
        self.sales_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
    
    def create_inventory_tab(self, notebook):
        frame = ttk.Frame(notebook)
        notebook.add(frame, text="库存查看")
        
        tree_frame = ttk.Frame(frame)
        tree_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        columns = ("id", "name", "category", "price", "stock", "total_value")
        self.inventory_tree = ttk.Treeview(tree_frame, columns=columns, show="headings")
        
        self.inventory_tree.heading("id", text="ID")
        self.inventory_tree.heading("name", text="商品名称")
        self.inventory_tree.heading("category", text="分类")
        self.inventory_tree.heading("price", text="单价")
        self.inventory_tree.heading("stock", text="库存数量")
        self.inventory_tree.heading("total_value", text="库存总值")
        
        self.inventory_tree.column("id", width=50)
        self.inventory_tree.column("name", width=150)
        self.inventory_tree.column("category", width=100)
        self.inventory_tree.column("price", width=80)
        self.inventory_tree.column("stock", width=80)
        self.inventory_tree.column("total_value", width=100)
        
        scrollbar = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL, command=self.inventory_tree.yview)
        self.inventory_tree.configure(yscrollcommand=scrollbar.set)
        
        self.inventory_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
    
    def add_product(self):
        try:
            name = self.product_name.get().strip()
            category = self.product_category.get().strip()
            price = float(self.product_price.get())
            stock = int(self.product_stock.get())
            
            if not name:
                messagebox.showerror("错误", "商品名称不能为空！")
                return
            
            self.db.add_product(name, category, price, stock)
            messagebox.showinfo("成功", "商品添加成功！")
            self.clear_product_inputs()
            self.refresh_products()
            self.refresh_inventory()
        except ValueError:
            messagebox.showerror("错误", "价格和数量必须是数字！")
        except Exception as e:
            messagebox.showerror("错误", f"添加失败: {str(e)}")
    
    def update_product(self):
        try:
            selected = self.product_tree.selection()
            if not selected:
                messagebox.showerror("错误", "请选择要更新的商品！")
                return
            
            item = self.product_tree.item(selected[0])
            product_id = item['values'][0]
            
            name = self.product_name.get().strip()
            category = self.product_category.get().strip()
            price = float(self.product_price.get())
            stock = int(self.product_stock.get())
            
            if not name:
                messagebox.showerror("错误", "商品名称不能为空！")
                return
            
            self.db.update_product(product_id, name, category, price, stock)
            messagebox.showinfo("成功", "商品更新成功！")
            self.clear_product_inputs()
            self.refresh_products()
            self.refresh_inventory()
        except ValueError:
            messagebox.showerror("错误", "价格和数量必须是数字！")
        except Exception as e:
            messagebox.showerror("错误", f"更新失败: {str(e)}")
    
    def delete_product(self):
        try:
            selected = self.product_tree.selection()
            if not selected:
                messagebox.showerror("错误", "请选择要删除的商品！")
                return
            
            item = self.product_tree.item(selected[0])
            product_id = item['values'][0]
            
            if messagebox.askyesno("确认", "确定要删除该商品吗？"):
                self.db.delete_product(product_id)
                messagebox.showinfo("成功", "商品删除成功！")
                self.clear_product_inputs()
                self.refresh_products()
                self.refresh_inventory()
        except Exception as e:
            messagebox.showerror("错误", f"删除失败: {str(e)}")
    
    def clear_product_inputs(self):
        self.product_name.delete(0, tk.END)
        self.product_category.delete(0, tk.END)
        self.product_price.delete(0, tk.END)
        self.product_stock.delete(0, tk.END)
    
    def on_product_select(self, event):
        selected = self.product_tree.selection()
        if selected:
            item = self.product_tree.item(selected[0])
            values = item['values']
            self.product_name.delete(0, tk.END)
            self.product_name.insert(0, values[1])
            self.product_category.delete(0, tk.END)
            self.product_category.insert(0, values[2])
            self.product_price.delete(0, tk.END)
            self.product_price.insert(0, values[3])
            self.product_stock.delete(0, tk.END)
            self.product_stock.insert(0, values[4])
    
    def register_purchase(self):
        try:
            product_id = int(self.purchase_product_id.get())
            quantity = int(self.purchase_quantity.get())
            price = float(self.purchase_price.get())
            supplier = self.purchase_supplier.get().strip()
            
            product = self.db.get_product(product_id)
            if product:
                self.db.purchase_product(product_id, quantity, price, supplier)
                messagebox.showinfo("成功", "进货登记成功！")
                self.clear_purchase_inputs()
                self.refresh_purchases()
                self.refresh_products()
                self.refresh_inventory()
            else:
                messagebox.showerror("错误", "商品不存在！")
        except ValueError:
            messagebox.showerror("错误", "请输入有效的数字！")
        except Exception as e:
            messagebox.showerror("错误", f"进货登记失败: {str(e)}")
    
    def clear_purchase_inputs(self):
        self.purchase_product_id.delete(0, tk.END)
        self.purchase_quantity.delete(0, tk.END)
        self.purchase_price.delete(0, tk.END)
        self.purchase_supplier.delete(0, tk.END)
    
    def register_sale(self):
        try:
            product_id = int(self.sales_product_id.get())
            quantity = int(self.sales_quantity.get())
            price = float(self.sales_price.get())
            customer = self.sales_customer.get().strip()
            
            product = self.db.get_product(product_id)
            if product:
                if product[4] >= quantity:
                    self.db.sell_product(product_id, quantity, price, customer)
                    messagebox.showinfo("成功", "销售登记成功！")
                    self.clear_sales_inputs()
                    self.refresh_sales()
                    self.refresh_products()
                    self.refresh_inventory()
                else:
                    messagebox.showerror("错误", "库存不足！")
            else:
                messagebox.showerror("错误", "商品不存在！")
        except ValueError:
            messagebox.showerror("错误", "请输入有效的数字！")
        except Exception as e:
            messagebox.showerror("错误", f"销售登记失败: {str(e)}")
    
    def clear_sales_inputs(self):
        self.sales_product_id.delete(0, tk.END)
        self.sales_quantity.delete(0, tk.END)
        self.sales_price.delete(0, tk.END)
        self.sales_customer.delete(0, tk.END)
    
    def refresh_products(self):
        for item in self.product_tree.get_children():
            self.product_tree.delete(item)
        
        products = self.db.get_all_products()
        for product in products:
            self.product_tree.insert("", tk.END, values=product)
    
    def refresh_purchases(self):
        for item in self.purchase_tree.get_children():
            self.purchase_tree.delete(item)
        
        purchases = self.db.get_purchases()
        for purchase in purchases:
            self.purchase_tree.insert("", tk.END, values=purchase)
    
    def refresh_sales(self):
        for item in self.sales_tree.get_children():
            self.sales_tree.delete(item)
        
        sales = self.db.get_sales()
        for sale in sales:
            self.sales_tree.insert("", tk.END, values=sale)
    
    def refresh_inventory(self):
        for item in self.inventory_tree.get_children():
            self.inventory_tree.delete(item)
        
        products = self.db.get_all_products()
        for product in products:
            total_value = product[3] * product[4]
            self.inventory_tree.insert("", tk.END, values=(*product, total_value))
    
    def on_closing(self):
        self.db.close()
        self.root.destroy()

def main():
    root = tk.Tk()
    app = InventoryApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()
