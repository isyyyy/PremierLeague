# Thiết kế miền tri thức cho hệ thống tri thức cầu thủ Premier League

## 1 Tổng quan

Hệ thống tri thức được thiết kế để quản lý thông tin về cầu thủ, câu lạc bộ và mùa giải của giải bóng đá Premier League.  Các nguồn dữ liệu chủ yếu lấy từ trang premierleague.com, nơi cung cấp hồ sơ cầu thủ, thống kê theo mùa và các nhóm thống kê như Attack, Physical, Defence và Discipline.  Việc phân tích nguồn dữ liệu này dẫn tới việc xây dựng ontology gồm các lớp (Classes), quan hệ (Object Properties) và thuộc tính dữ liệu (Datatype Properties) như dưới đây.

## 2 Lớp (Classes)

### 2.1 Player

Đại diện cho mỗi cầu thủ Premier League.

* **Thuộc tính chính**:

  * `name` – tên cầu thủ.
  * `dateOfBirth` – ngày sinh.
  * `nationality` – quốc tịch.
  * `preferredFoot` – chân thuận (Right/Left).
  * `height` – chiều cao.
  * `shirtNumber` – số áo hiện tại.
  * `joinedSeason` – mùa giải mà cầu thủ gia nhập CLB.
  * `totalAppearances`, `totalGoals`, `totalAssists` – số trận, bàn thắng và kiến tạo cộng dồn.
* **Quan hệ**:

  * `playsFor` → **Club** – cầu thủ thuộc CLB nào.
  * `hasPosition` → **Position** – vị trí thi đấu.
  * `hasNationality` → **Nationality** – quốc tịch.
  * `hasSeasonStats` → **PlayerSeasonStats** – liên kết tới thống kê của từng mùa.
  * `teammateWith` ↔ **Player** – đồng đội (quan hệ đối xứng; hai cầu thủ là đồng đội nếu cùng CLB trong cùng mùa).

### 2.2 Club

Đại diện cho câu lạc bộ tham dự Premier League.

* **Thuộc tính chính**: `clubName`, `foundationYear`, `stadium` (nếu có dữ liệu), `location`.
* **Quan hệ**:

  * `hasPlayer` → **Player** – các cầu thủ đang chơi cho CLB.
  * `participatesIn` → **Season** – CLB thi đấu trong mùa giải nào.
  * `hasSeasonStats` → **ClubSeasonStats** (tùy chọn) – thống kê của CLB theo mùa.

### 2.3 Season

Mô hình hóa mùa giải Premier League (ví dụ “2025/26”, “2024/25”).

* **Thuộc tính chính**: `seasonName` (nhãn mùa), `startYear`, `endYear`.  Thẻ chọn trên trang thống kê cho cầu thủ cho thấy các tùy chọn “All Seasons”, “2025/26”, “2022/23”.
* **Quan hệ**:

  * `includesPlayerSeasonStats` → **PlayerSeasonStats** – thống kê cầu thủ của mùa đó.
  * `includesClubSeasonStats` → **ClubSeasonStats** – thống kê CLB của mùa đó.

### 2.4 PlayerSeasonStats

Thể hiện thống kê của một cầu thủ trong một mùa giải cụ thể.  Điều này cho phép lưu trữ cùng lúc nhiều mùa cho một cầu thủ và hỗ trợ truy vấn theo mùa.

* **Thuộc tính chính**: các con số thống kê theo nhóm Attack, Physical, Defence và Discipline được trang premierleague.com cung cấp:

  * Attack: `appearances`, `goals`, `assists`, `expectedGoals (xG)`, `expectedAssists (xA)`, `touchesInBox`, `penaltiesTaken`, `hitWoodwork`, `freeKicksScored`, `crossesCompleted`.
  * Physical (thể lực): `minutesPlayed`, `dribblesCompleted`, `duelsWon`, `aerialDuelsWon`.
  * Defence: `tackles`, `interceptions`, `blocks`.
  * Discipline: `redCards`, `yellowCards`, `foulsCommitted`, `offsides`, `ownGoals`.
  * Possession/Other: `cornersTaken`, `passesCompleted`.
* **Quan hệ**:

  * `forPlayer` → **Player** – cầu thủ của bản ghi thống kê.
  * `forClub` → **Club** – CLB mà cầu thủ khoác áo trong mùa đó.
  * `inSeason` → **Season** – mùa giải tương ứng.
  * `hasStatCategory` → **StatCategory** (tùy chọn) – nhóm thống kê tương ứng.

## 3 Quan hệ giữa các lớp

Dưới đây là mô tả ngắn gọn các quan hệ chính và miền/đối tượng của chúng:

| Quan hệ             | Miền → Vùng giá trị              | Ý nghĩa                                                                    |
| ------------------- | -------------------------------- | -------------------------------------------------------------------------- |
| **playsFor**        | Player → Club                    | Cầu thủ hiện thuộc biên chế CLB nào.                                       |
| **hasSeasonStats**  | Player → PlayerSeasonStats       | Liên kết đến thống kê của cầu thủ trong từng mùa.                          |
| **teammateWith**    | Player ↔ Player                  | Quan hệ đối xứng; hai cầu thủ là đồng đội nếu cùng **Club** và **Season**. |
| **participatesIn**  | Club → Season                    | CLB tham dự mùa giải nào.                                                  |
| **hasPlayer**       | Club → Player                    | Danh sách cầu thủ thuộc CLB.                                               |
| **forPlayer**       | PlayerSeasonStats → Player       | Bản ghi thống kê thuộc về cầu thủ nào.                                     |
| **forClub**         | PlayerSeasonStats → Club         | CLB mà cầu thủ khoác áo trong mùa.                                         |
| **inSeason**        | PlayerSeasonStats → Season       | Mùa giải của bản ghi thống kê.                                             |


## 4 Lợi ích của thiết kế

1. **Truy vấn linh hoạt** – Có thể tìm cầu thủ theo thuộc tính tiểu sử (quốc tịch, vị trí, CLB) hoặc theo thống kê của một mùa cụ thể.  Việc tách thống kê theo lớp `PlayerSeasonStats` giúp trả lời câu hỏi như “ai ghi nhiều bàn nhất mùa 2024/25” hay “cầu thủ nào có nhiều pha tắc bóng nhất trong mùa vừa qua”.
2. **Suy luận** – Các thuộc tính thống kê là cơ sở để xây dựng luật suy luận, ví dụ: “IF goals > 100 AND assists > 50 THEN isLegend = true”.
3. **Mở rộng** – Ontology có thể mở rộng thêm `Match`, `Appearance` hoặc `ClubSeasonStats` khi cần dữ liệu chi tiết, đồng thời liên kết với các nguồn Linked Data khác như Wikidata hoặc DBpedia.

## 5 Citations

Các thuộc tính thống kê được xác định dựa trên các nhóm thống kê trên trang Stats của cầu thủ Premier League.  Ví dụ:

* Nhóm **Attack** liệt kê các chỉ số như Goals, Expected Goals (XG), Expected Assists (XA), Touches in the opposition box, Penalties taken, Hit woodwork, Free kicks scored, Crosses (completed %).
* Nhóm **Physical**, **Defence** và **Discipline** liệt kê Minutes played, Dribbles (completed %), Duels won, Aerial duels won, Total tackles, Interceptions, Blocks, Red cards, Yellow cards, Fouls, Offsides và Own goals.
* Hộp chọn mùa giải (“All Seasons”, “2025/26”, “2022/23”) trên trang thống kê xác nhận rằng dữ liệu được tổ chức theo mùa và cần mô hình lớp `Season`.
