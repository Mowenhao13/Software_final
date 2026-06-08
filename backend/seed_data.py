"""种子数据生成 — 生成100+条模拟供应链数据"""
import random
import math
from datetime import datetime, timedelta
from database import engine, SessionLocal, Base
from models import Supplier, Product, Inventory, Order, Shipment, RiskAlert, CostRecord


def seed_all():
    """初始化数据库并填充演示数据"""
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()

    # 防止重复填充
    if db.query(Supplier).count() > 0:
        db.close()
        print("数据库已有数据，跳过填充。")
        return

    # ========== 供应商 ==========
    supplier_data = [
        ("深圳华强电子", "电子元器件", "华南", "张伟", "138****1234", 92, 0.98, 0.99, 88, 8),
        ("北京神州数码", "IT设备", "华北", "李娜", "139****2345", 88, 0.95, 0.97, 82, 12),
        ("上海宝钢材料", "金属材料", "华东", "王强", "137****3456", 85, 0.92, 0.96, 90, 18),
        ("广州通达物流", "物流服务", "华南", "陈明", "136****4567", 78, 0.88, 0.95, 75, 6),
        ("成都精密制造", "精密零件", "西南", "刘洋", "135****5678", 90, 0.97, 0.98, 85, 15),
        ("武汉华中包装", "包装材料", "华中", "赵军", "134****6789", 82, 0.90, 0.94, 78, 24),
        ("南京金陵化工", "化工原料", "华东", "孙磊", "133****7890", 86, 0.93, 0.96, 83, 10),
        ("西安航天材料", "特种材料", "西北", "周杰", "132****8901", 94, 0.99, 0.99, 92, 20),
        ("杭州阿里云", "云服务", "华东", "吴婷", "131****9012", 91, 0.96, 0.98, 87, 4),
        ("重庆长安汽配", "汽车零部件", "西南", "郑鹏", "130****0123", 84, 0.91, 0.93, 80, 16),
    ]
    suppliers = []
    for s in supplier_data:
        sup = Supplier(name=s[0], category=s[1], region=s[2], contact=s[3], phone=s[4],
                       score=s[5], delivery_rate=s[6], quality_rate=s[7],
                       cost_score=s[8], response_time=s[9], status="active")
        db.add(sup)
        suppliers.append(sup)
    db.flush()

    # ========== 产品 ==========
    product_data = [
        ("MCU芯片-STM32", "MCU-001", "电子元器件", 12.5, suppliers[0].id, 14, 200),
        ("电容-100uF", "CAP-002", "电子元器件", 0.15, suppliers[0].id, 7, 5000),
        ("服务器主板", "SRV-001", "IT设备", 3500, suppliers[1].id, 21, 20),
        ("不锈钢板材304", "STL-001", "金属材料", 2800, suppliers[2].id, 10, 50),
        ("精密轴承-6205", "BRG-001", "精密零件", 45, suppliers[4].id, 14, 300),
        ("铝合金外壳", "ALU-001", "金属材料", 18, suppliers[2].id, 7, 500),
        ("塑料包装袋", "PKG-001", "包装材料", 0.8, suppliers[5].id, 5, 2000),
        ("环氧树脂AB胶", "CHM-001", "化工原料", 35, suppliers[6].id, 7, 150),
        ("钛合金螺栓", "TIT-001", "特种材料", 120, suppliers[7].id, 21, 100),
        ("云服务器ECS", "CLD-001", "云服务", 500, suppliers[8].id, 1, 0),
        ("汽车制动片", "BRK-001", "汽车零部件", 85, suppliers[9].id, 14, 200),
        ("PCB电路板", "PCB-001", "电子元器件", 3.5, suppliers[0].id, 10, 1000),
        ("铜线圈", "COP-001", "金属材料", 22, suppliers[2].id, 7, 300),
        ("齿轮箱体", "GRB-001", "精密零件", 380, suppliers[4].id, 21, 40),
        ("瓦楞纸箱", "CRT-001", "包装材料", 2.5, suppliers[5].id, 3, 1000),
    ]
    products = []
    for p in product_data:
        prod = Product(name=p[0], code=p[1], category=p[2], unit_price=p[3],
                       supplier_id=p[4], lead_time=p[5], min_stock=p[6])
        db.add(prod)
        products.append(prod)
    db.flush()

    # ========== 库存 ==========
    warehouses = ["华南中心仓", "华东仓", "华北仓", "西南仓", "华中仓"]
    inventories = []
    for i, prod in enumerate(products):
        qty = random.randint(prod.min_stock // 2, prod.min_stock * 3)
        inv = Inventory(product_id=prod.id, warehouse=random.choice(warehouses),
                        quantity=qty, safety_stock=prod.min_stock, max_stock=prod.min_stock * 10,
                        turnover_rate=round(random.uniform(1.5, 8.0), 1),
                        last_restock=datetime.now() - timedelta(days=random.randint(1, 30)))
        db.add(inv)
        inventories.append(inv)
    db.flush()

    # ========== 订单 ==========
    statuses = ["pending", "confirmed", "confirmed", "shipping", "shipping",
                "delivered", "delivered", "delivered", "delivered", "delivered", "delivered",
                "cancelled"]
    orders = []
    for i in range(60):
        prod = random.choice(products)
        qty = random.randint(100, 2000)
        order_date = datetime.now() - timedelta(days=random.randint(0, 90))
        status = random.choice(statuses)
        expected = order_date + timedelta(days=prod.lead_time + random.randint(0, 5))
        actual = expected + timedelta(days=random.randint(-2, 7)) if status == "delivered" else None
        if status == "cancelled":
            actual = None

        order = Order(
            order_no=f"PO-{datetime.now().year}-{i+1001:04d}",
            product_id=prod.id,
            supplier_id=prod.supplier_id,
            quantity=qty,
            amount=round(qty * prod.unit_price, 2),
            status=status,
            order_date=order_date,
            expected_delivery=expected,
            actual_delivery=actual,
        )
        db.add(order)
        orders.append(order)
    db.flush()

    # ========== 物流 ==========
    cities = [
        ("深圳", 114.07, 22.62), ("北京", 116.40, 39.90), ("上海", 121.47, 31.23),
        ("广州", 113.26, 23.13), ("成都", 104.07, 30.57), ("武汉", 114.30, 30.60),
        ("南京", 118.78, 32.07), ("西安", 108.93, 34.27), ("杭州", 120.15, 30.28),
        ("重庆", 106.55, 29.57), ("天津", 117.20, 39.12), ("长沙", 112.97, 28.23),
        ("昆明", 102.83, 24.88), ("郑州", 113.62, 34.75), ("哈尔滨", 126.53, 45.80),
    ]
    carriers = ["顺丰速运", "京东物流", "德邦物流", "中通快递", "圆通速递", "韵达快递"]
    modes = ["road", "road", "road", "air", "rail", "sea"]
    shipment_statuses = ["in_transit", "in_transit", "in_transit", "delivered", "delivered",
                         "delivered", "delayed"]

    for i, order in enumerate(orders[:40]):
        origin_city = random.choice(cities)
        dest_city = random.choice(cities)
        while dest_city == origin_city:
            dest_city = random.choice(cities)

        mode = random.choice(modes)
        cost = round(random.uniform(500, 15000), 2)
        if mode == "air":
            cost *= 2.5
        elif mode == "sea":
            cost *= 0.6

        dept = order.order_date + timedelta(days=random.randint(0, 3))
        eta = dept + timedelta(days=random.randint(1, 10))
        status = random.choice(shipment_statuses)
        actual_arrival = eta + timedelta(days=random.randint(-1, 3)) if status == "delivered" else None

        # 当前位置：在途时取中间点
        cur_lng = origin_city[1] + (dest_city[1] - origin_city[1]) * random.uniform(0.2, 0.8)
        cur_lat = origin_city[2] + (dest_city[2] - origin_city[2]) * random.uniform(0.2, 0.8)

        shipment = Shipment(
            tracking_no=f"SF{datetime.now().year}{100000+i:06d}",
            order_id=order.id,
            origin=origin_city[0],
            destination=dest_city[0],
            origin_lng=origin_city[1], origin_lat=origin_city[2],
            dest_lng=dest_city[1], dest_lat=dest_city[2],
            current_lng=cur_lng if status == "in_transit" else dest_city[1],
            current_lat=cur_lat if status == "in_transit" else dest_city[2],
            carrier=random.choice(carriers),
            transport_mode=mode,
            status=status,
            cost=cost,
            departure_time=dept,
            arrival_time=eta,
            actual_arrival=actual_arrival,
        )
        db.add(shipment)
    db.flush()

    # ========== 风险预警 ==========
    risk_data = [
        ("inventory_shortage", "high", "MCU芯片库存严重不足",
         "STM32芯片当前库存仅50件，低于安全库存200件，预计3天内将断货，影响3条生产线。",
         0.92, "product", products[0].id,
         "建议立即下单采购至少500件，并联系供应商加急处理。"),
        ("delivery_delay", "high", "华东仓发往华北的服务器主板延迟",
         "订单PO-2025-1003的服务器主板已延迟5天未到达，承运商反馈因天气原因。",
         0.85, "order", orders[2].id,
         "建议联系备选供应商，并评估对客户交付的影响。"),
        ("cost_spike", "medium", "不锈钢板材采购成本上升15%",
         "近30天不锈钢板材304的采购均价上涨15%，超出正常波动范围。",
         0.72, "product", products[3].id,
         "建议与供应商重新议价，或寻找替代材料。"),
        ("quality_issue", "high", "精密轴承批次质量问题",
         "供应商'成都精密制造'最近批次的精密轴承质量合格率降至92%，低于标准97%。",
         0.88, "supplier", suppliers[4].id,
         "已通知供应商整改，暂停该批次使用，启动质量追溯。"),
        ("supplier_risk", "medium", "广州通达物流服务评分持续下降",
         "该供应商近3个月综合评分从85降至78，主要因准时交付率下降。",
         0.68, "supplier", suppliers[3].id,
         "建议开展供应商评审，制定改进计划或寻找替代方案。"),
        ("inventory_shortage", "low", "包装材料库存偏高",
         "塑料包装袋库存周转率降至1.2，占用仓储资金，建议减少采购量。",
         0.35, "product", products[6].id,
         "建议暂停采购2周，优先消耗现有库存。"),
        ("delivery_delay", "medium", "西南地区物流时效下降",
         "发往昆明、重庆方向的物流时效近期平均延迟2.3天。",
         0.65, "shipment", 1,
         "建议优化西南地区物流路线，增加备选承运商。"),
        ("cost_spike", "medium", "环氧树脂原材料涨价预警",
         "受国际市场影响，环氧树脂AB胶原料价格预计下季度上涨8%-12%。",
         0.70, "product", products[7].id,
         "建议提前采购2-3个月用量，锁定当前价格。"),
        ("supplier_risk", "low", "杭州阿里云计费模式变更",
         "供应商计划下季度调整云服务计费模式，可能影响IT成本结构。",
         0.42, "supplier", suppliers[8].id,
         "关注变更详情，评估对整体IT预算的影响。"),
        ("inventory_shortage", "high", "汽车制动片库存告急",
         "当前库存80件，安全库存200件，且供应商交期14天，面临停产风险。",
         0.90, "product", products[10].id,
         "立即启动紧急采购流程，同时评估安全库存水平的合理性。"),
    ]
    for r in risk_data:
        alert = RiskAlert(
            alert_type=r[0], severity=r[1], title=r[2], description=r[3],
            risk_score=r[4], related_entity_type=r[5], related_entity_id=r[6],
            suggested_action=r[7], status="active" if r[4] > 0.5 else "acknowledged"
        )
        db.add(alert)
    db.flush()

    # ========== 成本记录 ==========
    cost_categories = ["procurement", "procurement", "procurement", "logistics", "logistics",
                       "inventory", "inventory", "quality", "quality", "other"]
    departments = ["采购部", "物流部", "仓储部", "质量部", "运营部"]
    for i in range(50):
        days_ago = random.randint(0, 180)
        cat = random.choice(cost_categories)
        cost = CostRecord(
            category=cat,
            subcategory=random.choice(["原材料", "运输费", "仓储租金", "检验费", "管理费"]),
            amount=round(random.uniform(1000, 50000), 2),
            department=random.choice(departments),
            date=(datetime.now() - timedelta(days=days_ago)),
            description=f"月度{cost_categories.index(cat)}类成本记录"
        )
        db.add(cost)

    db.commit()
    db.close()
    print("Seed data loaded: 10 suppliers, 15 products, 15 inventories, 60 orders, 40 shipments, 10 alerts, 50 cost records.")


if __name__ == "__main__":
    seed_all()
