from db.schema import init_db
from db import queries

init_db()

medicines = [
    ("Paracetamol 500", "PCM001", "2028-12-01", 250, 200, "Sun Pharma"),
    ("Azithromycin 500", "AZI002", "2027-09-01", 450, 150, "Cipla"),
    ("Amoxicillin 250", "AMX003", "2028-06-01", 320, 180, "Mankind"),
    ("Cetirizine", "CET004", "2027-10-01", 120, 250, "Dr. Reddy"),
    ("Pantoprazole", "PAN005", "2028-08-01", 480, 140, "Torrent"),
    ("Omeprazole", "OME006", "2027-11-01", 300, 120, "Sun Pharma"),
    ("Metformin 500", "MET007", "2028-07-01", 260, 300, "Lupin"),
    ("Telmisartan", "TEL008", "2029-01-01", 520, 160, "Cipla"),
    ("Amlodipine", "AML009", "2028-09-01", 210, 200, "Torrent"),
    ("Dolo 650", "DOL010", "2028-10-01", 310, 250, "Micro Labs"),
    ("Crocin", "CRO011", "2027-12-01", 290, 210, "GSK"),
    ("ORS Powder", "ORS012", None, 150, 300, "FDC"),
    ("Vitamin C", "VIT013", "2029-02-01", 200, 280, "Abbott"),
    ("Calcium Tablets", "CAL014", "2028-11-01", 380, 170, "Mankind"),
    ("Zinc Tablets", "ZIN015", "2027-06-01", 220, 140, "Cipla"),
    ("Diclofenac Gel", "DIC016", "2028-05-01", 180, 90, "Sun Pharma"),
    ("ORS Liquid", "ORS017", None, 130, 120, "FDC"),
    ("Insulin Pen", "INS018", "2027-04-01", 980, 60, "Novo Nordisk"),
    ("Cough Syrup", "COU019", "2027-08-01", 240, 110, "Benadryl"),
    ("Digene", "DIG020", "2028-03-01", 175, 130, "Abbott"),
    ("Electral", "ELE021", None, 95, 250, "FDC"),
    ("Volini Spray", "VOL022", "2028-09-01", 360, 80, "Sun Pharma"),
    ("Betadine", "BET023", "2028-06-01", 195, 100, "Win Medicare"),
    ("Liv52", "LIV024", "2029-01-01", 290, 140, "Himalaya"),
    ("ORS Kids", "ORS025", None, 120, 200, "FDC"),
]

for med in medicines:
    try:
        queries.add_medicine(
            name=med[0],
            batch_no=med[1],
            expiry_date=med[2],
            packet_price=med[3],
            stock=med[4],
            seller_name=med[5],
            packets=med[4],
            units_per_packet=1,
        )
    except Exception:
        pass

print("✅ Demo medicines added successfully.")