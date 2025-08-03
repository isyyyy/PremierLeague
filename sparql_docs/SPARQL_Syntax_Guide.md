# 📘 Giới thiệu cú pháp SPARQL

SPARQL là ngôn ngữ truy vấn dành cho dữ liệu dạng RDF . Tương tự như SQL nhưng dùng để truy xuất tri thức dạng "đồ thị" thay vì bảng.

---

## 🧱 Cấu trúc cơ bản của 1 câu truy vấn SPARQL

```sparql
PREFIX ex: <http://example.org/premierleague/>

SELECT ?player ?name
WHERE {
  ?player a ex:Player ;
          ex:hasName ?name .
}
LIMIT 10
```

### 📌 Giải thích:
- `PREFIX`: đặt alias cho URI để viết ngắn gọn
- `SELECT`: liệt kê các biến muốn truy xuất
- `WHERE`: phần điều kiện, mô tả mẫu (pattern) dữ liệu cần tìm
- `?var`: biến, đại diện cho thực thể, giá trị hoặc liên kết
- `a`: viết tắt cho `rdf:type`, nghĩa là "thuộc lớp"

🧠 RDF là dữ liệu dưới dạng triple:
```
Subject - Predicate - Object
```
Ví dụ:
```ttl
ex:player_100 ex:hasName "Marcus Rashford" .
```
---

## 🔎 Một số khái niệm RDF cơ bản

| Thành phần RDF     | Ý nghĩa                                      |
|--------------------|-----------------------------------------------|
| `rdf:type`         | một thực thể thuộc loại/lớp nào               |
| `rdfs:label`       | nhãn dễ đọc (dùng để hiển thị)                |
| `owl:ObjectProperty` | quan hệ giữa 2 thực thể                     |
| `owl:DatatypeProperty` | thuộc tính liên kết đến literal (int, str) |
| `xsd:string`, `xsd:date`, `xsd:int` | kiểu dữ liệu                   |

---

## ✏️ Các thành phần quan trọng trong SPARQL

### 1. `FILTER`
Dùng để lọc kết quả theo điều kiện.
```sparql
FILTER(?goals > 10)
```

### 2. `GROUP BY`, `COUNT`, `SUM`
Dùng cho thống kê, tổng hợp:
```sparql
SELECT ?nat (COUNT(?player) AS ?num)
WHERE {
  ?player ex:hasNationality ?nat .
}
GROUP BY ?nat
```

### 3. `ORDER BY`
Sắp xếp kết quả:
```sparql
ORDER BY DESC(?goals)
```

### 4. `LIMIT`
Giới hạn số lượng dòng trả về:
```sparql
LIMIT 10
```

---

## 📌 Ví dụ tổng hợp:
### 🎯 Lấy 10 cầu thủ ghi nhiều bàn nhất:
```sparql
PREFIX ex: <http://example.org/premierleague/>
SELECT ?player ?name ?goals
WHERE {
  ?player a ex:Player ;
          ex:hasName ?name ;
          ex:totalGoals ?goals .
}
ORDER BY DESC(?goals)
LIMIT 10
```

### 🧠 Tìm tất cả cầu thủ và CLB của họ:
```sparql
SELECT ?player ?name ?clubName
WHERE {
  ?player a ex:Player ;
          ex:hasName ?name ;
          ex:playsFor ?club .
  ?club ex:clubName ?clubName .
}
LIMIT 20
```

### 📊 Thống kê số cầu thủ theo quốc tịch:
```sparql
SELECT ?nat (COUNT(?player) AS ?numPlayers)
WHERE {
  ?player a ex:Player ;
          ex:hasNationality ?nat .
}
GROUP BY ?nat
ORDER BY DESC(?numPlayers)
```

---

### 🧑‍🤝‍🧑 4. Các cầu thủ là đồng đội của nhau
```sparql
SELECT ?p1 ?p2
WHERE {
  ?p1 ex:teammateWith ?p2 .
  FILTER(?p1 != ?p2)
}
LIMIT 20
```

### 🗓️ 5. Cầu thủ ghi bàn theo mùa
```sparql
SELECT ?player ?name ?season ?goals
WHERE {
  ?stat a ex:PlayerSeasonStats ;
        ex:forPlayer ?player ;
        ex:inSeason ?season ;
        ex:goals ?goals .
  ?player ex:hasName ?name .
}
ORDER BY DESC(?goals)
LIMIT 20
```


### 🏟️ 6. CLB và mùa giải họ tham gia
```sparql
SELECT ?club ?clubName ?season
WHERE {
  ?club a ex:Club ;
        ex:clubName ?clubName ;
        ex:participatesIn ?season .
}
LIMIT 20
```

### 🔢 7. Đếm số bản ghi thống kê theo mùa
```sparql
SELECT ?season (COUNT(?stat) AS ?numStats)
WHERE {
  ?season a ex:Season ;
          ex:includesPlayerSeasonStats ?stat .
}
GROUP BY ?season
ORDER BY DESC(?numStats)
```

### 🧾 8. Danh sách các vị trí thi đấu
```sparql
SELECT ?pos
WHERE {
  ?pos a ex:Position .
}
```

### 🧾 9. Lấy danh sách cầu thủ có số bàn lớn nhất của MU trong năm 2024
```sparql
PREFIX ex: <http://example.org/premierleague/>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>

# Lấy tất cả cầu thủ MU 2024 có goals = MAX
SELECT ?player ?name ?goals
WHERE {
  {
    # Subquery để tìm số bàn thắng cao nhất của MU mùa 2024
    SELECT (MAX(?g) AS ?topGoals)
    WHERE {
      ?stat a ex:PlayerSeasonStats ;
            ex:forClub ?club ;
            ex:inSeason ex:season_2024 ;
            ex:goals ?g .
      ?club ex:clubName "Manchester United" .
    }
  }

  # Cầu thủ nào thuộc MU và có số bàn = topGoals
  ?stat a ex:PlayerSeasonStats ;
        ex:forPlayer ?player ;
        ex:forClub ?club ;
        ex:inSeason ex:season_2024 ;
        ex:goals ?goals .

  ?player ex:hasName ?name .
  ?club ex:clubName "Manchester United" .
  FILTER(?goals = ?topGoals)
}

```