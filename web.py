import streamlit as st
import pandas as pd
import numpy as np
import io
from datetime import datetime
from congthuc import WaterSecurityIndicators

# Khởi tạo calculator từ congthuc.py (silent mode để không in ra console)
calc = WaterSecurityIndicators(silent=True)

# Cấu hình trang
st.set_page_config(
    page_title="Tính toán chỉ số An ninh nguồn nước sinh hoạt",
    layout="wide"
)

# Dữ liệu 24 chỉ số ANNN SH (An ninh nguồn nước sinh hoạt)
FORMULA_LATEX = {
    1: r"$M_0 = \frac{Q_{tb} \times 1000}{F}$",
    2: r"$M_{kiệt} = \frac{Q_{tb\_kiệt} \times 1000}{F}$",
    3: r"$C_{v\_kiệt} = \frac{\sigma}{\bar{X}}$",
    4: r"$\bar{X}_{năm} = \frac{\sum_{i=1}^{12} X_i}{12}$",
    5: r"$\Delta X = \frac{X_{năm\_i} - X_{năm\_j}}{X_{năm\_i}} \times 100$",
    6: r"$\Delta h = \frac{h_{năm\_i} - h_{năm\_j}}{h_{năm\_i}} \times 100$",
    7: r"$V_{trữ\_lượng}$ (Giá trị đo trực tiếp)",
    8: r"$T_{ngập\_lụt}$ (Giá trị đo trực tiếp)",
    9: r"$SPI = \frac{X - \bar{X}}{\sigma}$",
    10: r"$WSI_3$ (Giá trị đo trực tiếp)",
    11: r"$P_{CLN} = \frac{K}{k} \times 100$",
    12: r"$P_{hài\_lòng} = \frac{H}{h} \times 100$",
    13: r"$Q_{cấp\_nước} = \frac{W}{w}$",
    14: r"$T_{tình\_trạng} = \frac{M_{xc}}{m}$",
    15: r"$\Omega_{ổn\_định} = \frac{N}{n}$",
    16: r"$P_{tiếp\_cận} = \frac{P_{xl}}{P} \times 100$",
    17: r"$\Chi_{trả} = \frac{S}{S_{tn}} \times 100$",
    18: r"$\Chi_{chậm} = \frac{S_{chậm}}{W} \times 100$",
    19: r"$P_{phản\_ánh} = \frac{PA}{W} \times 100$",
    20: r"$NC_{tương\_lai}$ (Giá trị dự báo)",
    21: r"$CB = \frac{TC_{đô\_thị}}{TC_{nông\_thôn}} \times 100$",
    22: r"$QT = \frac{Z}{z} \times 100$",
    23: r"$P_{trường\_nước} = \frac{P}{p} \times 100$",
    24: r"$P_{trường\_VS} = \frac{Q}{p} \times 100$"
}
INDICATORS_DATA = [
    {
        "STT": 1,
        "Nhóm chỉ số": "Tiềm năng nguồn nước (Trữ lượng và Chất lượng)",
        "Chỉ thị": "Tiềm năng nước mặt (Mô đun dòng chảy năm)",
        "Biến số": "M0",
        "Công thức": "M0 = (Q_tb * 1000) / F",
        "Đơn vị": "l/s.km2",
        "Diễn giải": "Q_tb: Lưu lượng dòng chảy trung bình năm (m3/s); F: Diện tích lưu vực (km2)",
        "Ý nghĩa": "Mô đun dòng chảy năm (M0) thể hiện khả năng sản sinh nước trên lưu vực. M0 càng lớn thể hiện mức độ phong phú, sẵn có của nguồn nước. M0 càng lớn thì mức độ ANNN càng cao.",
        "Biến cần nhập": ["Q_tb", "F"]
    },
    {
        "STT": 2,
        "Nhóm chỉ số": "Tiềm năng nguồn nước (Trữ lượng và Chất lượng)",
        "Chỉ thị": "Tiềm năng nước mặt (Mô đun dòng chảy mùa kiệt)",
        "Biến số": "M_KIET",
        "Công thức": "M_kiet = (Q_tb_kiet * 1000) / F",
        "Đơn vị": "l/s.km2",
        "Diễn giải": "Q_tb_kiet: Lưu lượng dòng chảy trung bình mùa kiệt (m3/s); F: Diện tích lưu vực (km2)",
        "Ý nghĩa": "Mô đun dòng chảy kiệt (Mkiệt) thể hiện khả năng sản sinh nước trên lưu vực trong mùa kiệt. Mkiệt càng nhỏ thể hiện mức độ thiếu hụt nguồn nước càng lớn. Mkiệt càng lớn thì mức độ ANNN (mùa kiệt) càng tốt.",
        "Biến cần nhập": ["Q_tb_kiet", "F"]
    },
    {
        "STT": 3,
        "Nhóm chỉ số": "Tiềm năng nguồn nước (Trữ lượng và Chất lượng)",
        "Chỉ thị": "Tiềm năng nước mặt (Mức độ biến động dòng chảy kiệt)",
        "Biến số": "CV_KIET",
        "Công thức": "Cv_kiet = sigma / X_tb",
        "Đơn vị": "Không đơn vị",
        "Diễn giải": "sigma: Độ lệch chuẩn; X_tb: Giá trị trung bình",
        "Ý nghĩa": "Mức độ biến động dòng chảy mùa kiệt (Cv-kiệt) càng lớn tức độ phân tán của chuỗi số liệu dòng chảy mùa kiệt lớn nên khả năng xuất hiện những đợt hạn cực trị cao. Cv-kiệt càng cao càng mất ANNN",
        "Biến cần nhập": ["sigma", "X_tb"]
    },
    {
        "STT": 4,
        "Nhóm chỉ số": "Tiềm năng nguồn nước (Trữ lượng và Chất lượng)",
        "Chỉ thị": "Tiềm năng nước mưa",
        "Biến số": "LUONG_MUA_NAM",
        "Công thức": "X_tb_nam = (X1 + X2 + ... + X12) / 12",
        "Đơn vị": "mm",
        "Diễn giải": "X_i: Tổng lượng mưa bình quân tháng i (từ tháng 1 đến tháng 12)",
        "Ý nghĩa": "Tổng lượng nước đến do mưa phân bố ở các địa phương càng lớn thì mức độ ANNN càng cao.",
        "Biến cần nhập": ["X1", "X2", "X3", "X4", "X5", "X6", "X7", "X8", "X9", "X10", "X11", "X12"]
    },
    {
        "STT": 5,
        "Nhóm chỉ số": "Tiềm năng nguồn nước (Trữ lượng và Chất lượng)",
        "Chỉ thị": "Xu thế biến đổi lượng mưa dưới tác động của BĐKH",
        "Biến số": "TL_MUA_THAYDOI",
        "Công thức": "((X_nam_i - X_nam_j) / X_nam_i) * 100",
        "Đơn vị": "%",
        "Diễn giải": "X_nam_i: Lượng mưa năm i; X_nam_j: Lượng mưa năm j",
        "Ý nghĩa": "Lượng mưa thay đổi ảnh hưởng đến nguồn nước trong khu vực, nếu lượng mưa tăng sẽ tăng thêm trữ lượng nước trên các lưu vực sông",
        "Biến cần nhập": ["X_nam_i", "X_nam_j"]
    },
    {
        "STT": 6,
        "Nhóm chỉ số": "Tiềm năng nguồn nước (Trữ lượng và Chất lượng)",
        "Chỉ thị": "Xu thế thay đổi mực nước ngầm",
        "Biến số": "TL_NUOCNGAM_THAYDOI",
        "Công thức": "((h_nam_i - h_nam_j) / h_nam_i) * 100",
        "Đơn vị": "%",
        "Diễn giải": "h_nam_i: Mực nước ngầm năm i; h_nam_j: Mực nước ngầm năm j",
        "Ý nghĩa": "Khả năng bổ sung nguồn nước từ nước ngầm, tiềm năng nước ngầm càng lớn mức độ ANNN càng cao.",
        "Biến cần nhập": ["h_nam_i", "h_nam_j"]
    },
    {
        "STT": 7,
        "Nhóm chỉ số": "Tiềm năng nguồn nước (Trữ lượng và Chất lượng)",
        "Chỉ thị": "Tổng lượng nước trong các hồ chứa phục vụ cấp nước sinh hoạt",
        "Biến số": "TRULUONG_HOCHUA",
        "Công thức": "V_tru_luong",
        "Đơn vị": "10^6 m3",
        "Diễn giải": "V_reservoirs: Trữ lượng nước trong các hồ chứa lớn tại đầu mùa kiệt",
        "Ý nghĩa": "Trên địa bàn có nhiều hồ chứa (thủy lợi/ thủy điện) thì khả năng giữ nước lại trên lưu vực càng cao, tăng mức đảm bảo cung cấp nước đáp ứng các nhu cầu sử dụng tại địa phương, tỷ lệ này cao chứng tỏ mức độ ANNN đối với vùng được hưởng lợi tốt. Lượng nước trong hồ chứa tại thời điểm đánh giá càng nhiều sẽ đảm bảo đủ nguồn nước cấp cho sinh hoạt",
        "Biến cần nhập": ["V_reservoirs"]
    },
    {
        "STT": 8,
        "Nhóm chỉ số": "Tiềm năng nguồn nước (Trữ lượng và Chất lượng)",
        "Chỉ thị": "Thời gian ngập lụt trung bình hàng năm",
        "Biến số": "THOIGIAN_NGAPLUT",
        "Công thức": "T_ngap_lut",
        "Đơn vị": "Giờ",
        "Diễn giải": "flood_hours: Thời gian ngập lụt trung bình hàng năm",
        "Ý nghĩa": "Đánh giá nguy cơ ngập lụt làm ảnh hưởng đến nguồn nước sinh hoạt",
        "Biến cần nhập": ["flood_hours"]
    },
    {
        "STT": 9,
        "Nhóm chỉ số": "Tiềm năng nguồn nước (Trữ lượng và Chất lượng)",
        "Chỉ thị": "Mức độ hạn hán trong khu vực",
        "Biến số": "SPI",
        "Công thức": "SPI = (X - X_mean) / sigma",
        "Đơn vị": "Không đơn vị",
        "Diễn giải": "X: Lượng mưa tính toán; X_mean: Lượng mưa TB; sigma_spi: Độ lệch chuẩn",
        "Ý nghĩa": "Địa phương có mức độ hạn hán nhiều ảnh hưởng nhiều đến khả năng cung cấp nước phục vụ cho các ngành. Chỉ số này càng cao thì ANNN càng thấp.",
        "Biến cần nhập": ["X", "X_mean", "sigma_spi"]
    },
    {
        "STT": 10,
        "Nhóm chỉ số": "Tiềm năng nguồn nước (Trữ lượng và Chất lượng)",
        "Chỉ thị": "Mức độ xâm nhập mặn",
        "Biến số": "WSI3",
        "Công thức": "WSI3",
        "Đơn vị": "‰",
        "Diễn giải": "salinity_val: Mức độ ảnh hưởng của xâm nhập mặn",
        "Ý nghĩa": "Mức độ nhiễm mặn càng lớn ảnh hưởng đến nguồn nước cấp cho người dân và các nhà máy nước sử dụng nguồn nước sông",
        "Biến cần nhập": ["salinity_val"]
    },
    {
        "STT": 11,
        "Nhóm chỉ số": "Tiềm năng nguồn nước (Trữ lượng và Chất lượng)",
        "Chỉ thị": "Chất lượng nước mặt tại các sông/hồ trong khu vực (xã/phường)",
        "Biến số": "SO_LAN_VUOT_NGUONG",
        "Công thức": "P_cln = (K / k) * 100",
        "Đơn vị": "%",
        "Diễn giải": "K: Số lần vượt ngưỡng QC 08/2023; k: Tổng số lần lấy mẫu",
        "Ý nghĩa": "Thể hiện khả năng nguồn nước tự nhiên trong khu vực có đáp ứng được cho sinh hoạt",
        "Biến cần nhập": ["K", "k"]
    },
    {
        "STT": 12,
        "Nhóm chỉ số": "Tiềm năng nguồn nước (Trữ lượng và Chất lượng)",
        "Chỉ thị": "Mức độ hài lòng của người dân về chất lượng nước sinh hoạt",
        "Biến số": "TL_HAILONG_CLN",
        "Công thức": "P_hai_long = (H / h) * 100",
        "Đơn vị": "%",
        "Diễn giải": "H: Số hộ KHÔNG hài lòng; h: Tổng số hộ được cấp nước",
        "Ý nghĩa": "Mức độ hài lòng của người dân về chất lượng nước sinh hoạt",
        "Biến cần nhập": ["H", "h"]
    },
    {
        "STT": 13,
        "Nhóm chỉ số": "Hạ tầng phân bổ nguồn nước (Khả năng tiếp cận và tính ổn định)",
        "Chỉ thị": "Năng lực cấp nước từ các công trình cấp nước sạch",
        "Biến số": "MUCDO_CONGTRINH",
        "Công thức": "Cap_nuoc = W / w",
        "Đơn vị": "m3/người/ngày",
        "Diễn giải": "W: Tổng công suất cấp nước (m3/ngày); w: Tổng dân số (người)",
        "Ý nghĩa": "Tổng công suất cấp nước của các nhà máy so với tổng dân số có đáp ứng theo quy chuẩn nước sạch thành thị và nông thôn?",
        "Biến cần nhập": ["W_13", "w_13"]
    },
    {
        "STT": 14,
        "Nhóm chỉ số": "Hạ tầng phân bổ nguồn nước (Khả năng tiếp cận và tính ổn định)",
        "Chỉ thị": "Tình trạng các công trình khai thác và cấp nước sinh hoạt trên địa bàn",
        "Biến số": "CONGSUAT_CAPNUOC",
        "Công thức": "Tinh_trang = M_xc / m",
        "Đơn vị": "Tỷ lệ",
        "Diễn giải": "M_xc: Số công trình xuống cấp; m: Tổng số công trình",
        "Ý nghĩa": "Tình trạng các công trình khai thác và cấp nước thể hiện sự ổn định, hoàn thiện của các công trình cấp nước đến các hộ dùng nước",
        "Biến cần nhập": ["M_xc", "m"]
    },
    {
        "STT": 15,
        "Nhóm chỉ số": "Hạ tầng phân bổ nguồn nước (Khả năng tiếp cận và tính ổn định)",
        "Chỉ thị": "Mức độ ổn định của hệ thống cấp nước sinh hoạt",
        "Biến số": "SO_NGAY_MAT_NUOC",
        "Công thức": "On_dinh = N / n",
        "Đơn vị": "ngày/năm",
        "Diễn giải": "N: Số ngày mất nước không kế hoạch; n: Tổng số ngày trong năm (365)",
        "Ý nghĩa": "Số ngày mất nước trong năm gần đó càng ít thì mức độ ổn định của hệ thống càng cao",
        "Biến cần nhập": ["N", "n"]
    },
    {
        "STT": 16,
        "Nhóm chỉ số": "Hạ tầng phân bổ nguồn nước (Khả năng tiếp cận và tính ổn định)",
        "Chỉ thị": "Khả năng người dân tiếp cận nguồn nước sạch tại địa phương",
        "Biến số": "TL_TIEPCAN_NUOCSACH",
        "Công thức": "P_tiep_can = (P_xl / P) * 100",
        "Đơn vị": "%",
        "Diễn giải": "P_xl: Số người dân được cấp nước sạch; P: Tổng dân số khu vực",
        "Ý nghĩa": "Đánh giá khả năng tiếp cận nguồn nước sạch từng vùng",
        "Biến cần nhập": ["P_xl", "P"]
    },
    {
        "STT": 17,
        "Nhóm chỉ số": "Hộ sử dụng nước",
        "Chỉ thị": "Khả năng chi trả tiền của người dân",
        "Biến số": "TL_TIEN_NUOC",
        "Công thức": "Chi_tra = (S / S_tn) * 100",
        "Đơn vị": "%",
        "Diễn giải": "S: Chi phí tiền nước; S_tn: Tổng thu nhập hộ dân",
        "Ý nghĩa": "Đánh giá khả chi trả tiền nước sạch của người dân",
        "Biến cần nhập": ["S", "S_tn"]
    },
    {
        "STT": 18,
        "Nhóm chỉ số": "Hộ sử dụng nước",
        "Chỉ thị": "Mức độ khó khăn trong chi trả tiền nguồn nước",
        "Biến số": "TL_CHAM_TRA",
        "Công thức": "Cham_tra = (S_cham / W) * 100",
        "Đơn vị": "%",
        "Diễn giải": "S_cham: Số hộ chậm trả tiền nước; W_18: Tổng số hộ được cấp nước",
        "Ý nghĩa": "Đánh giá mức độ khó khăn trong thanh toán/tiếp cận nguồn nước",
        "Biến cần nhập": ["S_cham", "W_18"]
    },
    {
        "STT": 19,
        "Nhóm chỉ số": "Hộ sử dụng nước",
        "Chỉ thị": "Mức độ hài lòng của người dân về nguồn nước sử dụng hiện tại",
        "Biến số": "TL_KHIEUNAI",
        "Công thức": "Phan_anh = (PA / W) * 100",
        "Đơn vị": "%",
        "Diễn giải": "PA: Số hộ phản ánh, khiếu nại; W_19: Tổng số hộ được cấp nước",
        "Ý nghĩa": "Phản ảnh mức độ hài lòng của người dân về nguồn nước",
        "Biến cần nhập": ["PA", "W_19"]
    },
    {
        "STT": 20,
        "Nhóm chỉ số": "Hộ sử dụng nước",
        "Chỉ thị": "Nhu cầu sử dụng nước trong tương lai",
        "Biến số": "MUCDO_GIATANG_NHUCAU",
        "Công thức": "Nhu_cau_tuong_lai",
        "Đơn vị": "%",
        "Diễn giải": "demand_increase: Mức độ gia tăng nhu cầu dùng nước trong 2-5 năm tới (%)",
        "Ý nghĩa": "Đánh giá xu thế thay đổi nhu cầu dùng nước của người dân trong tương lai",
        "Biến cần nhập": ["demand_increase"]
    },
    {
        "STT": 21,
        "Nhóm chỉ số": "Tính công bằng trong sử dụng nguồn nước sinh hoạt và phúc lợi trẻ em",
        "Chỉ thị": "Tính công bằng trong tiếp cận nguồn nước giữa các vùng",
        "Biến số": "TL_TIEPCAN_DOTHI_NONGTHON",
        "Công thức": "Cong_bang = (TC_dt / TC_nt) * 100",
        "Đơn vị": "%",
        "Diễn giải": "TC_dt: % hộ đô thị tiếp cận nước sạch; TC_nt: % hộ nông thôn tiếp cận nước sạch",
        "Ý nghĩa": "Phản ánh tính công bằng trong tiếp cận nguồn nước giữa các vùng",
        "Biến cần nhập": ["TC_dt", "TC_nt"]
    },
    {
        "STT": 22,
        "Nhóm chỉ số": "Tính công bằng trong sử dụng nguồn nước sinh hoạt và phúc lợi trẻ em",
        "Chỉ thị": "Mức độ quan tâm đến ANNN trong chỉ đạo, điều hành",
        "Biến số": "MUCDO_HOANTHIEN_VANBAN",
        "Công thức": "Quan_tam = (Z / z) * 100",
        "Đơn vị": "%",
        "Diễn giải": "Z: Số văn bản hướng dẫn ANNN; z: Tổng số văn bản liên quan cấp nước",
        "Ý nghĩa": "Phản ảnh mức độ quan tâm của các cơ quan chức năng đến cấp nước sinh hoạt",
        "Biến cần nhập": ["Z", "z"]
    },
    {
        "STT": 23,
        "Nhóm chỉ số": "Tính công bằng trong sử dụng nguồn nước sinh hoạt và phúc lợi trẻ em",
        "Chỉ thị": "Khả năng tiếp cận nguồn nước sạch tại các trường học/cơ sở giáo dục",
        "Biến số": "TL_TRUONGHOC_NUOCSACH",
        "Công thức": "Truong_hoc_nuoc = (P / p) * 100",
        "Đơn vị": "%",
        "Diễn giải": "P_school: Số trường có nước sạch thường xuyên; p_total: Tổng số trường học",
        "Ý nghĩa": "Phản ảnh % trường học / cơ sở giáo dục có nước uống an toàn, sẵn có cho trẻ em",
        "Biến cần nhập": ["P_school", "p_total"]
    },
    {
        "STT": 24,
        "Nhóm chỉ số": "Tính công bằng trong sử dụng nguồn nước sinh hoạt và phúc lợi trẻ em",
        "Chỉ thị": "Các cơ sở giáo dục có khu vệ sinh đạt yêu cầu cho trẻ em",
        "Biến số": "TL_CSGD_VESINH",
        "Công thức": "Truong_hoc_vsinh = (Q / p) * 100",
        "Đơn vị": "%",
        "Diễn giải": "Q_school: Số trường có khu vệ sinh/rửa tay đạt chuẩn; p_total_24: Tổng số trường học",
        "Ý nghĩa": "Các cơ sở giáo dục có khu vệ sinh đạt yêu cầu cho trẻ em phản ánh khả năng tiếp cận thực tế trẻ em đối với nước sinh hoạt an toàn",
        "Biến cần nhập": ["Q_school", "p_total_24"]
    }
]

# Công thức LaTeX hiển thị đẹp cho từng chỉ số
FORMULA_LATEX = {
    1: r"$M_0 = \frac{Q_{tb} \times 1000}{F}$",
    2: r"$M_{kiệt} = \frac{Q_{tb\_kiệt} \times 1000}{F}$",
    3: r"$C_{v\_kiệt} = \frac{\sigma}{\bar{X}}$",
    4: r"$\bar{X}_{năm} = \frac{\sum_{i=1}^{12} X_i}{12}$",
    5: r"$\Delta X = \frac{X_{năm\_i} - X_{năm\_j}}{X_{năm\_i}} \times 100$",
    6: r"$\Delta h = \frac{h_{năm\_i} - h_{năm\_j}}{h_{năm\_i}} \times 100$",
    7: r"$V_{trữ\_lượng}$ (Giá trị đo trực tiếp)",
    8: r"$T_{ngập\_lụt}$ (Giá trị đo trực tiếp)",
    9: r"$SPI = \frac{X - \bar{X}}{\sigma}$",
    10: r"$WSI_3$ (Giá trị đo trực tiếp)",
    11: r"$P_{CLN} = \frac{K}{k} \times 100$",
    12: r"$P_{hài\_lòng} = \frac{H}{h} \times 100$",
    13: r"$Q_{cấp\_nước} = \frac{W}{w}$",
    14: r"$T_{tình\_trạng} = \frac{M_{xc}}{m}$",
    15: r"$\Omega_{ổn\_định} = \frac{N}{n}$",
    16: r"$P_{tiếp\_cận} = \frac{P_{xl}}{P} \times 100$",
    17: r"$\Chi_{trả} = \frac{S}{S_{tn}} \times 100$",
    18: r"$\Chi_{chậm} = \frac{S_{chậm}}{W} \times 100$",
    19: r"$P_{phản\_ánh} = \frac{PA}{W} \times 100$",
    20: r"$NC_{tương\_lai}$ (Giá trị dự báo)",
    21: r"$CB = \frac{TC_{đô\_thị}}{TC_{nông\_thôn}} \times 100$",
    22: r"$QT = \frac{Z}{z} \times 100$",
    23: r"$P_{trường\_nước} = \frac{P}{p} \times 100$",
    24: r"$P_{trường\_VS} = \frac{Q}{p} \times 100$"
}

# Hàm tính toán theo từng chỉ số - gọi hàm từ congthuc.py
def calculate_by_indicator(stt, variables):
    """Tính toán giá trị dựa trên chỉ số và biến số đã nhập, gọi hàm từ congthuc.py"""
    try:
        if stt == 1:  # Mô đun dòng chảy năm
            Q_tb = variables.get('Q_tb', 0)
            F = variables.get('F', 1)
            if F == 0: return None
            return calc.calculate_idx_1(Q_tb=Q_tb, F=F)
        
        elif stt == 2:  # Mô đun dòng chảy mùa kiệt
            Q_tb_kiet = variables.get('Q_tb_kiet', 0)
            F = variables.get('F', 1)
            if F == 0: return None
            return calc.calculate_idx_2(Q_tb_kiet=Q_tb_kiet, F=F)
        
        elif stt == 3:  # Mức độ biến động dòng chảy kiệt
            sigma = variables.get('sigma', 0)
            X_tb = variables.get('X_tb', 1)
            if X_tb == 0: return None
            return calc.calculate_idx_3(sigma=sigma, X_tb=X_tb)
        
        elif stt == 4:  # Tổng lượng mưa bình quân năm
            # Lấy lượng mưa 12 tháng
            rain_months = [
                variables.get('X1', 0), variables.get('X2', 0), variables.get('X3', 0),
                variables.get('X4', 0), variables.get('X5', 0), variables.get('X6', 0),
                variables.get('X7', 0), variables.get('X8', 0), variables.get('X9', 0),
                variables.get('X10', 0), variables.get('X11', 0), variables.get('X12', 0)
            ]
            return calc.calculate_idx_4(rain_months=rain_months)
        
        elif stt == 5:  # Tỷ lệ % lượng mưa thay đổi
            X_nam_i = variables.get('X_nam_i', 0)
            X_nam_j = variables.get('X_nam_j', 0)
            if X_nam_i == 0: return None
            return calc.calculate_idx_5(X_nam_i=X_nam_i, X_nam_j=X_nam_j)
        
        elif stt == 6:  # Tỷ lệ thay đổi mực nước ngầm
            h_nam_i = variables.get('h_nam_i', 0)
            h_nam_j = variables.get('h_nam_j', 0)
            if h_nam_i == 0: return None
            return calc.calculate_idx_6(h_nam_i=h_nam_i, h_nam_j=h_nam_j)
        
        elif stt == 7:  # Trữ lượng nước trong hồ chứa
            V_reservoirs = variables.get('V_reservoirs', 0)
            return calc.info_idx_7(V_reservoirs=V_reservoirs)
        
        elif stt == 8:  # Thời gian ngập lụt
            flood_hours = variables.get('flood_hours', 0)
            return calc.info_idx_8(flood_hours=flood_hours)
        
        elif stt == 9:  # Chỉ số hạn hán SPI
            X = variables.get('X', 0)
            X_mean = variables.get('X_mean', 0)
            sigma = variables.get('sigma_spi', 1)
            if sigma == 0: return None
            return calc.calculate_idx_9(X=X, X_mean=X_mean, sigma=sigma)
        
        elif stt == 10:  # Xâm nhập mặn
            salinity_val = variables.get('salinity_val', 0)
            return calc.info_idx_10(salinity_val=salinity_val)
        
        elif stt == 11:  # Chất lượng nước mặt
            K = variables.get('K', 0)
            k = variables.get('k', 1)
            if k == 0: return None
            return calc.calculate_idx_11(K=K, k=k)
        
        elif stt == 12:  # Mức độ hài lòng về chất lượng nước
            H = variables.get('H', 0)
            h = variables.get('h', 1)
            if h == 0: return None
            return calc.calculate_idx_12(H=H, h=h)
        
        elif stt == 13:  # Năng lực cấp nước
            W = variables.get('W_13', 0)
            w = variables.get('w_13', 1)
            if w == 0: return None
            return calc.calculate_idx_13(W=W, w=w)
        
        elif stt == 14:  # Tình trạng công trình
            M_xc = variables.get('M_xc', 0)
            m = variables.get('m', 1)
            if m == 0: return None
            return calc.calculate_idx_14(M_xc=M_xc, m=m)
        
        elif stt == 15:  # Mức độ ổn định hệ thống
            N = variables.get('N', 0)
            n = variables.get('n', 365)
            if n == 0: return None
            return calc.calculate_idx_15(N=N, n=n)
        
        elif stt == 16:  # Khả năng tiếp cận nước sạch
            P_xl = variables.get('P_xl', 0)
            P = variables.get('P', 1)
            if P == 0: return None
            return calc.calculate_idx_16(P_xl=P_xl, P=P)
        
        elif stt == 17:  # Khả năng chi trả
            S = variables.get('S', 0)
            S_tn = variables.get('S_tn', 1)
            if S_tn == 0: return None
            return calc.calculate_idx_17(S=S, S_tn=S_tn)
        
        elif stt == 18:  # Khó khăn trong chi trả
            S_cham = variables.get('S_cham', 0)
            W_total = variables.get('W_18', 1)
            if W_total == 0: return None
            return calc.calculate_idx_18(S_cham=S_cham, W_total=W_total)
        
        elif stt == 19:  # Mức độ hài lòng qua khiếu nại
            PA = variables.get('PA', 0)
            W_total = variables.get('W_19', 1)
            if W_total == 0: return None
            return calc.calculate_idx_19(PA=PA, W_total=W_total)
        
        elif stt == 20:  # Nhu cầu tương lai
            demand_increase = variables.get('demand_increase', 0)
            return calc.info_idx_20(demand_increase=demand_increase)
        
        elif stt == 21:  # Tính công bằng đô thị - nông thôn
            TC_dt = variables.get('TC_dt', 0)
            TC_nt = variables.get('TC_nt', 1)
            if TC_nt == 0: return None
            return calc.calculate_idx_21(TC_dt=TC_dt, TC_nt=TC_nt)
        
        elif stt == 22:  # Mức độ quan tâm của chính quyền
            Z = variables.get('Z', 0)
            z_total = variables.get('z', 1)
            if z_total == 0: return None
            return calc.calculate_idx_22(Z=Z, z_total=z_total)
        
        elif stt == 23:  # Tiếp cận nước sạch tại trường học
            P_school = variables.get('P_school', 0)
            p_total = variables.get('p_total', 1)
            if p_total == 0: return None
            return calc.calculate_idx_23(P_school=P_school, p_total=p_total)
        
        elif stt == 24:  # Vệ sinh đạt chuẩn tại trường học
            Q_school = variables.get('Q_school', 0)
            p_total = variables.get('p_total_24', 1)
            if p_total == 0: return None
            return calc.calculate_idx_24(Q_school=Q_school, p_total=p_total)
        
        return None
    except Exception as e:
        return f"Lỗi: {str(e)}"

# Hàm tính toán công thức (backward compatible)
def calculate_formula(formula, variables, stt=None):
    """Tính toán giá trị dựa trên công thức và biến số đã nhập"""
    if stt is not None:
        return calculate_by_indicator(stt, variables)
    
    if not formula or formula.strip() == "":
        return None
    
    try:
        # Thay thế các biến trong công thức bằng giá trị
        result_formula = formula
        for var_name, var_value in variables.items():
            if var_value is not None:
                result_formula = result_formula.replace(var_name, str(var_value))
        
        # Tính toán công thức
        result = eval(result_formula)
        return round(result, 4)
    except Exception as e:
        return f"Lỗi: {str(e)}"

# Hàm lấy tất cả biến cần nhập từ các chỉ số đã chọn
def get_all_input_variables(selected_indicators):
    """Lấy danh sách tất cả các biến cần nhập từ các chỉ số đã chọn"""
    all_vars = {}
    for indicator in selected_indicators:
        for var in indicator["Biến cần nhập"]:
            if var not in all_vars:
                all_vars[var] = {
                    "indicators": [indicator["Chỉ thị"]],
                    "dien_giai": indicator["Diễn giải"]
                }
            else:
                all_vars[var]["indicators"].append(indicator["Chỉ thị"])
    return all_vars

# Màu nền cho từng nhóm chỉ số
GROUP_COLORS = {
    "Tiềm năng nguồn nước (Trữ lượng và Chất lượng)": "#E3F2FD",  # Xanh nhạt
    "Hạ tầng phân bổ nguồn nước (Khả năng tiếp cận và tính ổn định)": "#E8F5E9",  # Xanh lá nhạt
    "Hộ sử dụng nước": "#FFF3E0",  # Cam nhạt
    "Tính công bằng trong sử dụng nguồn nước sinh hoạt và phúc lợi trẻ em": "#F3E5F5"  # Tím nhạt
}

# 13 chỉ số ANNN SH cơ bản (STT)
BASIC_INDICATORS = [2, 4, 6, 7, 11, 13, 15, 16, 19, 20, 21, 23, 24]
BASIC_INDICATOR_COLOR = "#FCE4EC"  # Màu hồng nhạt

# Khởi tạo session state
if "page" not in st.session_state:
    st.session_state.page = 1
if "selected_indicators" not in st.session_state:
    st.session_state.selected_indicators = []
if "input_values" not in st.session_state:
    st.session_state.input_values = {}
if "csv_values" not in st.session_state:
    st.session_state.csv_values = {}
if "results" not in st.session_state:
    st.session_state.results = {}
if "results_csv" not in st.session_state:
    st.session_state.results_csv = {}
if "select_all" not in st.session_state:
    st.session_state.select_all = False
if "select_basic" not in st.session_state:
    st.session_state.select_basic = False
if "group_selections" not in st.session_state:
    st.session_state.group_selections = {}
if "indicator_selections" not in st.session_state:
    st.session_state.indicator_selections = {}

# Tiêu đề chính
st.title("Hệ thống tính toán chỉ số An ninh nguồn nước sinh hoạt (ANNN SH)")

# Sidebar hiển thị tiến trình
st.sidebar.title("📌 Tiến trình")
pages = ["1. Chọn chỉ số", "2. Nhập giá trị", "3. Tính toán", "4. So sánh"]
for i, p in enumerate(pages, 1):
    if i == st.session_state.page:
        st.sidebar.markdown(f"**➡️ {p}**")
    elif i < st.session_state.page:
        st.sidebar.markdown(f"✅ {p}")
    else:
        st.sidebar.markdown(f"⬜ {p}")

# ==================== GIAO DIỆN 1: CHỌN CHỈ SỐ ====================
if st.session_state.page == 1:
    st.header("📋 Giao diện 1: Lựa chọn các chỉ số ANNN SH muốn tính")
    
    st.info("Vui lòng chọn các chỉ số bạn muốn tính toán từ danh sách 24 chỉ số dưới đây.")
    
    # Tạo DataFrame để hiển thị
    df_display = pd.DataFrame([{
        "STT": ind["STT"],
        "Nhóm chỉ số": ind["Nhóm chỉ số"],
        "Chỉ thị": ind["Chỉ thị"],
        "Biến số": ind["Biến số"],
        "Công thức": ind["Công thức"] if ind["Công thức"] else "(Nhập trực tiếp)",
        "Đơn vị": ind["Đơn vị"],
        "Diễn giải": ind["Diễn giải"],
        "Ý nghĩa": ind["Ý nghĩa"],
        "Cơ bản": "✓" if ind["STT"] in BASIC_INDICATORS else ""
    } for ind in INDICATORS_DATA])
    
    # Hàm tô màu hồng cho 13 chỉ số cơ bản
    def highlight_basic_indicators(row):
        if row['STT'] in BASIC_INDICATORS:
            return [f'background-color: {BASIC_INDICATOR_COLOR}'] * len(row)
        return [''] * len(row)
    
    # Hiển thị bảng chỉ số với màu nền
    styled_df = df_display.style.apply(highlight_basic_indicators, axis=1)
    st.dataframe(styled_df, width='stretch', height=400)
    
    st.markdown(f"**📌 Chú thích:** <span style='background-color: {BASIC_INDICATOR_COLOR}; padding: 2px 8px; border-radius: 3px;'>13 chỉ số ANNN SH cơ bản</span>", unsafe_allow_html=True)
    
    st.subheader("🔘 Chọn các chỉ số muốn tính toán:")
    
    # Tổ chức theo nhóm chỉ số
    groups = {}
    for ind in INDICATORS_DATA:
        group = ind["Nhóm chỉ số"]
        if group not in groups:
            groups[group] = []
        groups[group].append(ind)
    
    # Callback cho nút chọn tất cả
    def on_select_all_change():
        new_value = st.session_state.chk_select_all
        st.session_state.select_all = new_value
        # Cập nhật tất cả các nhóm
        for group_name in groups.keys():
            st.session_state.group_selections[group_name] = new_value
        # Cập nhật tất cả các chỉ số
        for ind in INDICATORS_DATA:
            st.session_state.indicator_selections[ind["STT"]] = new_value
        # Cập nhật trạng thái select_basic
        if new_value:
            st.session_state.select_basic = True
        else:
            st.session_state.select_basic = False
    
    # Callback cho nút chọn 13 chỉ số cơ bản
    def on_select_basic_change():
        new_value = st.session_state.chk_select_basic
        st.session_state.select_basic = new_value
        # Cập nhật 13 chỉ số cơ bản
        for stt in BASIC_INDICATORS:
            st.session_state.indicator_selections[stt] = new_value
        # Cập nhật trạng thái các nhóm
        for group_name, indicators in groups.items():
            group_all_selected = all(st.session_state.indicator_selections.get(ind["STT"], False) for ind in indicators)
            st.session_state.group_selections[group_name] = group_all_selected
        # Cập nhật trạng thái select_all
        all_selected = all(st.session_state.indicator_selections.get(ind["STT"], False) for ind in INDICATORS_DATA)
        st.session_state.select_all = all_selected
    
    # Callback cho nút chọn nhóm
    def on_group_change(group_name):
        group_selected = st.session_state[f"chk_group_{group_name}"]
        st.session_state.group_selections[group_name] = group_selected
        for ind in groups[group_name]:
            st.session_state.indicator_selections[ind["STT"]] = group_selected
        # Cập nhật trạng thái select_all
        all_selected = all(st.session_state.indicator_selections.get(ind["STT"], False) for ind in INDICATORS_DATA)
        st.session_state.select_all = all_selected
    
    # Callback cho từng chỉ số
    def on_indicator_change(stt, group_name):
        st.session_state.indicator_selections[stt] = st.session_state[f"chk_{stt}"]
        # Cập nhật trạng thái nhóm
        group_all_selected = all(st.session_state.indicator_selections.get(ind["STT"], False) for ind in groups[group_name])
        st.session_state.group_selections[group_name] = group_all_selected
        # Cập nhật trạng thái select_all
        all_selected = all(st.session_state.indicator_selections.get(ind["STT"], False) for ind in INDICATORS_DATA)
        st.session_state.select_all = all_selected
        # Cập nhật trạng thái select_basic
        basic_all_selected = all(st.session_state.indicator_selections.get(s, False) for s in BASIC_INDICATORS)
        st.session_state.select_basic = basic_all_selected
    
    # Chọn tất cả và chọn 13 chỉ số cơ bản
    col_all1, col_all2, col_all3 = st.columns([1, 1.5, 2.5])
    with col_all1:
        st.checkbox("**🔘 Chọn tất cả**", 
                   value=st.session_state.select_all, 
                   key="chk_select_all",
                   on_change=on_select_all_change)
    with col_all2:
        st.checkbox("**🌟 Chọn 13 chỉ số cơ bản**", 
                   value=st.session_state.select_basic, 
                   key="chk_select_basic",
                   on_change=on_select_basic_change,
                   help="Chọn 13 chỉ số ANNN SH cơ bản được đánh dấu màu hồng trong bảng")
    
    for group_name, indicators in groups.items():
        # Checkbox cho nhóm
        group_selected = st.session_state.group_selections.get(group_name, False)
        col_group1, col_group2 = st.columns([1, 4])
        with col_group1:
            st.checkbox(f"**📁 {group_name}**", 
                       value=group_selected,
                       key=f"chk_group_{group_name}",
                       on_change=on_group_change,
                       args=(group_name,))
        
        # Các chỉ số trong nhóm
        cols = st.columns(3)
        for i, ind in enumerate(indicators):
            with cols[i % 3]:
                ind_selected = st.session_state.indicator_selections.get(ind["STT"], False)
                st.checkbox(f"{ind['STT']}. {ind['Chỉ thị']}", 
                           value=ind_selected, 
                           key=f"chk_{ind['STT']}",
                           on_change=on_indicator_change,
                           args=(ind["STT"], group_name))
        st.markdown("---")
    
    st.divider()
    
    col1, col2 = st.columns([1, 1])
    with col2:
        if st.button("Tiếp theo ➡️", type="primary", width='stretch'):
            # Lấy danh sách các chỉ số đã chọn từ session state
            selected_stts = [stt for stt, selected in st.session_state.indicator_selections.items() if selected]
            if selected_stts:
                st.session_state.selected_indicators = [
                    ind for ind in INDICATORS_DATA if ind["STT"] in selected_stts
                ]
                st.session_state.page = 2
                st.rerun()
            else:
                st.error("Vui lòng chọn ít nhất 1 chỉ số!")

# ==================== GIAO DIỆN 2: NHẬP GIÁ TRỊ ====================
elif st.session_state.page == 2:
    st.header("📝 Giao diện 2: Nhập giá trị cho các biến số")
    
    # Hiển thị các chỉ số đã chọn
    st.subheader("📌 Các chỉ số đã chọn:")
    selected_df = pd.DataFrame([{
        "STT": ind["STT"],
        "Chỉ thị": ind["Chỉ thị"],
        "Biến số": ind["Biến số"],
        "Công thức": ind["Công thức"] if ind["Công thức"] else "(Nhập trực tiếp)"
    } for ind in st.session_state.selected_indicators])
    st.dataframe(selected_df, width='stretch', hide_index=True)
    
    st.divider()
    
    # Lấy tất cả biến cần nhập
    all_input_vars = get_all_input_variables(st.session_state.selected_indicators)
    
    # Tab nhập liệu
    tab1, tab2 = st.tabs(["📤 Nhập từ file CSV (Giá trị quá khứ)", "✏️ Nhập trực tiếp (Giá trị mới)"])
    
    with tab1:
        st.info("Tải lên nhiều file CSV chứa các giá trị đã có sẵn. Mỗi file CSV cần có cột 'Biến số' và 'Giá trị'. Bạn có thể tải lên nhiều file khác nhau cho các biến số khác nhau.")
        
        uploaded_files = st.file_uploader(
            "Chọn các file CSV (có thể chọn nhiều file)", 
            type=['csv'], 
            key="csv_upload",
            accept_multiple_files=True
        )
        
        if uploaded_files:
            total_vars_imported = 0
            for uploaded_file in uploaded_files:
                try:
                    df_csv = pd.read_csv(uploaded_file, encoding='utf-8')
                    st.success(f"✅ Đọc file '{uploaded_file.name}' thành công!")
                    
                    with st.expander(f"📄 Xem nội dung file: {uploaded_file.name}"):
                        st.dataframe(df_csv, width='stretch')
                    
                    # Lưu giá trị từ CSV
                    if 'Biến số' in df_csv.columns and 'Giá trị' in df_csv.columns:
                        vars_imported = 0
                        for _, row in df_csv.iterrows():
                            var_name = row['Biến số']
                            var_value = row['Giá trị']
                            if var_name in all_input_vars:
                                st.session_state.csv_values[var_name] = var_value
                                vars_imported += 1
                        total_vars_imported += vars_imported
                        st.info(f"📥 Đã nhập {vars_imported} biến số từ file '{uploaded_file.name}'")
                    else:
                        st.warning(f"⚠️ File '{uploaded_file.name}' cần có cột 'Biến số' và 'Giá trị'")
                except Exception as e:
                    st.error(f"❌ Lỗi đọc file '{uploaded_file.name}': {str(e)}")
            
            if total_vars_imported > 0:
                st.success(f"🎉 Tổng cộng đã nhập {len(st.session_state.csv_values)} giá trị từ các file CSV!")
        
        # Hiển thị các biến đã nhập từ CSV
        if st.session_state.csv_values:
            with st.expander("📋 Các biến số đã nhập từ CSV", expanded=True):
                csv_df = pd.DataFrame([
                    {"Biến số": k, "Giá trị": v} 
                    for k, v in st.session_state.csv_values.items()
                ])
                st.dataframe(csv_df, width='stretch', hide_index=True)
                
                if st.button("🗑️ Xóa tất cả giá trị CSV"):
                    st.session_state.csv_values = {}
                    st.rerun()
        
        # Hiển thị mẫu file CSV
        with st.expander("📄 Xem mẫu file CSV"):
            sample_data = {
                "Biến số": list(all_input_vars.keys())[:5],
                "Giá trị": [100, 200, 0.3, 1000, 50000][:len(list(all_input_vars.keys())[:5])]
            }
            st.dataframe(pd.DataFrame(sample_data))
            
            # Tải xuống mẫu
            csv_sample = pd.DataFrame({
                "Biến số": list(all_input_vars.keys()),
                "Giá trị": [0] * len(all_input_vars)
            })
            st.download_button(
                "⬇️ Tải xuống mẫu CSV",
                csv_sample.to_csv(index=False, encoding='utf-8-sig'),
                "mau_nhap_lieu.csv",
                "text/csv"
            )
    
    with tab2:
        st.info("Nhập trực tiếp các giá trị hiện tại hoặc dự báo tương lai.")
        
        st.subheader("📊 Danh sách biến số cần nhập:")
        
        # Nhóm các biến theo chỉ thị
        for indicator in st.session_state.selected_indicators:
            with st.expander(f"📌 {indicator['STT']}. {indicator['Chỉ thị']}", expanded=True):
                # Hiển thị công thức đẹp với LaTeX
                latex_formula = FORMULA_LATEX.get(indicator['STT'], indicator['Công thức'])
                st.markdown(f"**Công thức:** {latex_formula}")
                st.markdown(f"**Đơn vị kết quả:** {indicator['Đơn vị']}")
                
                # Hiển thị diễn giải và ý nghĩa
                col_info1, col_info2 = st.columns(2)
                with col_info1:
                    st.info(f"📖 **Diễn giải:** {indicator['Diễn giải']}")
                with col_info2:
                    st.info(f"💡 **Ý nghĩa:** {indicator['Ý nghĩa']}")
                
                # Input fields cho các biến
                cols = st.columns(len(indicator["Biến cần nhập"]))
                for i, var in enumerate(indicator["Biến cần nhập"]):
                    with cols[i]:
                        # Lấy giá trị mặc định từ session state
                        default_val = st.session_state.input_values.get(var, 0.0)
                        
                        # Tạo tooltip từ diễn giải
                        help_text = None
                        if var in indicator["Diễn giải"]:
                            parts = indicator["Diễn giải"].split(", ")
                            for part in parts:
                                if var in part:
                                    help_text = part
                                    break
                        
                        value = st.number_input(
                            f"**{var}**",
                            value=default_val,
                            format="%.4f",
                            key=f"input_{indicator['STT']}_{var}",
                            help=help_text
                        )
                        st.session_state.input_values[var] = value
    
    st.divider()
    
    # Nút điều hướng
    col1, col2, col3 = st.columns([1, 1, 1])
    with col1:
        if st.button("⬅️ Quay lại", width='stretch'):
            st.session_state.page = 1
            st.rerun()
    
    with col3:
        if st.button("Tính toán ➡️", type="primary", width='stretch'):
            # Kiểm tra xem có đủ giá trị không
            has_input = len(st.session_state.input_values) > 0
            has_csv = len(st.session_state.csv_values) > 0
            
            if has_input or has_csv:
                st.session_state.page = 3
                st.rerun()
            else:
                st.error("Vui lòng nhập ít nhất một giá trị!")

# ==================== GIAO DIỆN 3: TÍNH TOÁN ====================
elif st.session_state.page == 3:
    st.header("🔢 Giao diện 3: Kết quả tính toán")
    
    # Tính toán kết quả
    results_new = []  # Kết quả từ giá trị nhập trực tiếp
    results_csv = []  # Kết quả từ giá trị CSV
    
    for indicator in st.session_state.selected_indicators:
        stt = indicator["STT"]
        
        # Tính từ giá trị nhập trực tiếp
        if st.session_state.input_values:
            result_new = calculate_by_indicator(stt, st.session_state.input_values)
            if result_new is None:
                # Nếu không tính được, thử lấy giá trị trực tiếp
                result_new = st.session_state.input_values.get(indicator["Biến cần nhập"][0], None)
            
            results_new.append({
                "STT": indicator["STT"],
                "Nhóm chỉ số": indicator["Nhóm chỉ số"],
                "Chỉ thị": indicator["Chỉ thị"],
                "Biến số": indicator["Biến số"],
                "Công thức": indicator["Công thức"] if indicator["Công thức"] else "(Nhập trực tiếp)",
                "Giá trị ANNN SH mới": round(result_new, 4) if isinstance(result_new, (int, float)) else result_new,
                "Đơn vị": indicator["Đơn vị"]
            })
        
        # Tính từ giá trị CSV
        if st.session_state.csv_values:
            result_csv = calculate_by_indicator(stt, st.session_state.csv_values)
            if result_csv is None:
                result_csv = st.session_state.csv_values.get(indicator["Biến cần nhập"][0], None)
            
            results_csv.append({
                "STT": indicator["STT"],
                # "Nhóm chỉ số": indicator["Nhóm chỉ số"],
                "Chỉ thị": indicator["Chỉ thị"],
                # "Biến số": indicator["Biến số"],
                # "Công thức": indicator["Công thức"] if indicator["Công thức"] else "(Nhập trực tiếp)",
                "Giá trị ANNN SH quá khứ": round(result_csv, 4) if isinstance(result_csv, (int, float)) else result_csv,
                "Đơn vị": indicator["Đơn vị"]
            })
    
    # Hàm tạo màu nền cho bảng theo nhóm chỉ số
    def highlight_by_group(row):
        group = row['Nhóm chỉ số']
        color = GROUP_COLORS.get(group, '#FFFFFF')
        return [f'background-color: {color}'] * len(row)
    
    # Hiển thị kết quả
    if results_new and results_csv:
        st.subheader("📊 Kết quả tính toán (So sánh)")
        
        # Kết hợp kết quả
        combined_results = []
        for i, res_new in enumerate(results_new):
            combined = res_new.copy()
            combined["Giá trị ANNN SH quá khứ"] = results_csv[i]["Giá trị ANNN SH quá khứ"]
            combined_results.append(combined)
        
        df_results = pd.DataFrame(combined_results)
        # Áp dụng màu nền theo nhóm
        styled_df = df_results.style.apply(highlight_by_group, axis=1)
        st.dataframe(styled_df, width='stretch', hide_index=True)
        
        # Hiển thị chú thích màu
        st.markdown("**📌 Chú thích màu theo nhóm chỉ số:**")
        legend_cols = st.columns(len(GROUP_COLORS))
        for i, (group, color) in enumerate(GROUP_COLORS.items()):
            with legend_cols[i]:
                st.markdown(f"<div style='background-color: {color}; padding: 5px; border-radius: 5px; font-size: 12px;'>{group[:30]}...</div>", unsafe_allow_html=True)
        
        st.session_state.results = combined_results
        
    elif results_new:
        st.subheader("📊 Kết quả tính toán (Giá trị mới)")
        df_results = pd.DataFrame(results_new)
        # Áp dụng màu nền theo nhóm
        styled_df = df_results.style.apply(highlight_by_group, axis=1)
        st.dataframe(styled_df, width='stretch', hide_index=True)
        
        # Hiển thị chú thích màu
        st.markdown("**📌 Chú thích màu theo nhóm chỉ số:**")
        legend_cols = st.columns(len(GROUP_COLORS))
        for i, (group, color) in enumerate(GROUP_COLORS.items()):
            with legend_cols[i]:
                st.markdown(f"<div style='background-color: {color}; padding: 5px; border-radius: 5px; font-size: 12px;'>{group[:30]}...</div>", unsafe_allow_html=True)
        
        st.session_state.results = results_new
        
    elif results_csv:
        st.subheader("📊 Kết quả tính toán (Giá trị quá khứ từ CSV)")
        df_results = pd.DataFrame(results_csv)
        # Áp dụng màu nền theo nhóm
        styled_df = df_results.style.apply(highlight_by_group, axis=1)
        st.dataframe(styled_df, width='stretch', hide_index=True)
        
        # Hiển thị chú thích màu
        st.markdown("**📌 Chú thích màu theo nhóm chỉ số:**")
        legend_cols = st.columns(len(GROUP_COLORS))
        for i, (group, color) in enumerate(GROUP_COLORS.items()):
            with legend_cols[i]:
                st.markdown(f"<div style='background-color: {color}; padding: 5px; border-radius: 5px; font-size: 12px;'>{group[:30]}...</div>", unsafe_allow_html=True)
        
        st.session_state.results = results_csv
    
    # Hiển thị chi tiết từng chỉ số
    st.divider()
    st.subheader("📋 Chi tiết kết quả từng chỉ số:")
    
    for indicator in st.session_state.selected_indicators:
        with st.expander(f"📌 {indicator['STT']}. {indicator['Chỉ thị']}", expanded=False):
            col1, col2 = st.columns(2)
            with col1:
                st.markdown(f"**Biến số:** `{indicator['Biến số']}`")
                # Hiển thị công thức đẹp với LaTeX
                latex_formula = FORMULA_LATEX.get(indicator['STT'], indicator['Công thức'])
                st.markdown(f"**Công thức:** {latex_formula}")
                st.markdown(f"**Đơn vị:** {indicator['Đơn vị']}")
            
            with col2:
                st.markdown(f"**Diễn giải:** {indicator['Diễn giải']}")
                st.markdown(f"**Ý nghĩa:** {indicator['Ý nghĩa']}")
            
            st.markdown("**Giá trị các biến đã nhập:**")
            var_values = {}
            for var in indicator["Biến cần nhập"]:
                val_new = st.session_state.input_values.get(var, "N/A")
                val_csv = st.session_state.csv_values.get(var, "N/A")
                var_values[var] = {"Giá trị mới": val_new, "Giá trị CSV": val_csv}
            
            st.dataframe(pd.DataFrame(var_values).T, width='stretch')
    
    st.divider()
    
    # Nút điều hướng
    col1, col2, col3 = st.columns([1, 1, 1])
    with col1:
        if st.button("⬅️ Quay lại", width='stretch'):
            st.session_state.page = 2
            st.rerun()
    
    with col2:
        # Lưu kết quả
        if st.session_state.results:
            df_save = pd.DataFrame(st.session_state.results)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            csv_data = df_save.to_csv(index=False, encoding='utf-8-sig')
            
            st.download_button(
                "💾 Lưu kết quả (CSV)",
                csv_data,
                f"ketqua_ANNNSH_{timestamp}.csv",
                "text/csv",
                width='stretch'
            )
    
    with col3:
        if st.button("So sánh kết quả ➡️", type="primary", width='stretch'):
            st.session_state.page = 4
            st.rerun()

# ==================== GIAO DIỆN 4: SO SÁNH KẾT QUẢ ====================
elif st.session_state.page == 4:
    st.header("📈 Giao diện 4: So sánh kết quả các lần tính toán")
    
    st.info("Tải lên các file CSV kết quả tính toán đã được lưu trước đó để so sánh.")
    
    # Upload nhiều file
    uploaded_files = st.file_uploader(
        "Chọn các file CSV kết quả (có thể chọn nhiều file)",
        type=['csv'],
        accept_multiple_files=True,
        key="compare_upload"
    )
    
    if uploaded_files:
        all_dfs = []
        file_names = []
        
        for i, file in enumerate(uploaded_files):
            try:
                df = pd.read_csv(file, encoding='utf-8')
                # Thêm cột để phân biệt file
                df['Nguồn'] = file.name
                all_dfs.append(df)
                file_names.append(file.name)
                st.success(f"✅ Đọc file '{file.name}' thành công!")
            except Exception as e:
                st.error(f"❌ Lỗi đọc file '{file.name}': {str(e)}")
        
        if len(all_dfs) >= 1:
            st.divider()
            st.subheader("📊 Bảng so sánh kết quả")
            
            # Tạo bảng so sánh
            if len(all_dfs) == 1:
                st.dataframe(all_dfs[0], width='stretch', hide_index=True)
            else:
                # Pivot để so sánh theo chỉ thị
                combined_df = pd.concat(all_dfs, ignore_index=True)
                
                # Hiển thị bảng gốc
                st.markdown("**📋 Dữ liệu gộp từ tất cả các file:**")
                st.dataframe(combined_df, width='stretch', hide_index=True)
                
                # Thử tạo bảng pivot nếu có cột phù hợp
                try:
                    if 'Chỉ thị' in combined_df.columns:
                        st.divider()
                        st.markdown("**📈 So sánh theo chỉ thị:**")
                        
                        # Xác định cột giá trị
                        value_cols = [col for col in combined_df.columns if 'Giá trị' in col]
                        
                        if value_cols:
                            for val_col in value_cols:
                                if val_col in combined_df.columns:
                                    pivot_df = combined_df.pivot_table(
                                        index='Chỉ thị',
                                        columns='Nguồn',
                                        values=val_col,
                                        aggfunc='first'
                                    )
                                    
                                    st.markdown(f"**{val_col}:**")
                                    st.dataframe(pivot_df, width='stretch')
                                    
                                    # Vẽ biểu đồ so sánh
                                    if len(pivot_df.columns) > 1:
                                        st.bar_chart(pivot_df)
                except Exception as e:
                    st.warning(f"Không thể tạo bảng pivot: {str(e)}")
            
            # So sánh chi tiết
            st.divider()
            st.subheader("📊 Biểu đồ so sánh")
            
            if len(all_dfs) >= 2:
                # Tạo biểu đồ nếu có cột số
                for df in all_dfs:
                    numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
                    if numeric_cols and 'STT' not in numeric_cols:
                        st.markdown(f"**Biểu đồ từ {df['Nguồn'].iloc[0]}:**")
                        chart_cols = [c for c in numeric_cols if 'STT' not in c]
                        if chart_cols:
                            st.line_chart(df[chart_cols])
    
    else:
        st.warning("Vui lòng tải lên ít nhất 1 file CSV để xem hoặc so sánh kết quả.")
        
        # Hiển thị kết quả hiện tại nếu có
        if st.session_state.results:
            st.divider()
            st.subheader("📋 Kết quả tính toán hiện tại")
            df_current = pd.DataFrame(st.session_state.results)
            st.dataframe(df_current, width='stretch', hide_index=True)
    
    st.divider()
    
    # Nút điều hướng
    col1, col2, col3 = st.columns([1, 1, 1])
    with col1:
        if st.button("⬅️ Quay lại", width='stretch'):
            st.session_state.page = 3
            st.rerun()
    
    with col2:
        if st.button("🏠 Về trang đầu", width='stretch'):
            st.session_state.page = 1
            st.session_state.selected_indicators = []
            st.session_state.input_values = {}
            st.session_state.csv_values = {}
            st.session_state.results = {}
            st.rerun()

# Footer
st.sidebar.divider()
st.sidebar.markdown("---")
st.sidebar.markdown("📊 **Hệ thống ANNN SH**")
st.sidebar.markdown("Version 1.0")
