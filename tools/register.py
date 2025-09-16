PLC_REGISTERS = {
    "A": [
        {"code": f"A{i}", "reg": "D100", "button": "D1000", "lamp": "D1010"}
        for i in range(1, 51)
    ],
    "B": [
        {"code": f"B{i}", "reg": "D104", "button": "D1004", "lamp": "D1014"}
        for i in range(1, 51)
    ],
    "C": [
        {"code": f"C{i}", "reg": "D107", "button": "D1007", "lamp": "D1017"}
        for i in range(1, 51)
    ],
    "D": [
        {"code": f"D{i}", "reg": "D110", "button": "D1020", "lamp": "D1030"}
        for i in range(1, 51)
    ],
    "E": [
        {"code": f"E{i}", "reg": "D114", "button": "D1024", "lamp": "D1034"}
        for i in range(1, 51)
    ],
    "F": [
        {
            "code": f"F{i}",
            "reg": "D119" if i in [3, 14, 17] else "D117",
            "button": "D1028" if i in [3, 14, 17] else "D1027",
            "lamp": "D1038" if i in [3, 14, 17] else "D1037",
        }
        for i in range(1, 51)
    ],
    "AA": [
        {"code": f"AA{i}", "reg": "D120", "button": "D1040", "lamp": "D1050"}
        for i in range(1, 51)
    ],
    "AB": [
        {"code": f"AB{i}", "reg": "D124", "button": "D1043", "lamp": "D1053"}
        for i in range(1, 51)
    ],
}
