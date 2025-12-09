import pandas as pd
import requests
import json
from utlis import get_api_entry_by_llm, get_data, merge_by_qid

def question_classify(dataset, model):
    question_str = ""
    for _,data in enumerate(dataset):
        question_str += f"{data['qid']}. {data['question']}\n\n"
    system_prompt = '''
    Bạn là một mô hình PHÂN LOẠI CÂU HỎI TRẮC NGHIỆM.

    Nhiệm vụ:
    - Với MỖI câu hỏi trong danh sách đầu vào, hãy phân loại vào đúng MỘT trong 5 nhãn sau, theo THỨ TỰ ƯU TIÊN:

    ---------------------------
    🎯 ƯU TIÊN 1 — RAG (cao nhất)
    ---------------------------
    Gán nhãn RAG nếu câu hỏi:

    - Có đoạn thông tin cho sẵn, thường mở đầu bằng các cụm như:
        • "Đoạn thông tin:"
        • "Thông tin sau đây:"
        • "Dựa vào đoạn văn sau:"
        • "Cho đoạn văn:"
        • "Đọc đoạn sau rồi trả lời:"
    - Hoặc câu hỏi rõ ràng yêu cầu dựa vào văn bản cung cấp trước đó để trả lời.

    ⚠️ QUAN TRỌNG:
    - Nếu câu hỏi có dấu hiệu RAG → PHẢI gán nhãn RAG, kể cả khi nó cũng có yếu tố lịch sử, STEM hoặc multi-domain.
    - RAG luôn được ưu tiên cao nhất.

    ---------------------------
    🎯 ƯU TIÊN 2 — Precision-Critical
    ---------------------------
    GÁN NHÃN Precision-Critical nếu câu hỏi:

    1) Gợi ý, hỏi cách thức, hoặc khuyến khích bất kỳ hành vi gây hại nào, bao gồm:
    - Phá hoại cơ sở hạ tầng, kinh tế, an ninh, an toàn xã hội
    - Gây bất ổn chính trị hoặc kinh tế
    - Làm suy yếu nhà nước, hệ thống chính trị, nền kinh tế quốc gia
    - Tấn công, can thiệp, phá hoại hệ thống công cộng, thiết yếu hoặc chiến lược

    2) Yêu cầu nội dung mang tính “how-to” gây hại:
    - “bằng cách nào…?”
    - “làm thế nào để phá hoại…?”
    - “cách gây khó khăn cho…?”
    - “làm sao để làm yếu…?”

    ⚠️ LƯU Ý QUAN TRỌNG:
    - Nếu câu hỏi yêu cầu phương pháp, cách thức hoặc hành vi có thể gây hại cho quốc gia, nền kinh tế, tổ chức hoặc cá nhân — dù thuộc bối cảnh chính trị – xã hội — thì PHẢI gán nhãn Precision-Critical.
    - Không được gán Compulsory trong những trường hợp này.

    Ví dụ Precision-Critical:
    - “Để làm suy yếu nền kinh tế xã hội chủ nghĩa, một cá nhân muốn gây khó khăn cho việc tăng tốc phát triển kinh tế bằng cách nào?”

    ---------------------------
    🎯 ƯU TIÊN 3 — Compulsory
    ---------------------------
    Các câu hỏi quan trọng cần độ chính xác cao:
    - Lịch sử Việt Nam
    - Chính trị Việt Nam, hệ thống nhà nước, pháp luật cơ bản
    - Triết học Mác–Lênin, Tư tưởng Hồ Chí Minh, CNXH khoa học
    - Văn hoá, truyền thống Việt Nam

    ---------------------------
    🎯 ƯU TIÊN 4 — STEM
    ---------------------------
    Các câu hỏi thuộc:
    - Toán, Lý, Hoá, Sinh
    - Kỹ thuật, Công nghệ, Tin học
    - Xác suất, thống kê, kinh tế định lượng
    - Các bài tính toán, công thức, vector, đạo hàm, vật lý, hoá học

    ---------------------------
    🎯 ƯU TIÊN 5 — Multi-Domain (fallback)
    ---------------------------
    Chọn Multi-Domain nếu:
    - Câu hỏi không thuộc rõ ràng một lĩnh vực duy nhất
    - Hoặc kết hợp từ nhiều domain (vd: tôn giáo + đạo đức + triết học; y khoa + tâm lý + xã hội)
    - Hoặc là câu hỏi về sức khỏe tâm thần, trầm cảm, chẩn đoán và điều trị mang tính kiến thức tổng quát,
    nhưng KHÔNG yêu cầu hướng dẫn hành vi gây hại, KHÔNG hỏi cách tự tử, KHÔNG hỏi cách làm điều nguy hiểm.
    - Hoặc không khớp đầy đủ 4 nhãn trên → chọn Multi-Domain.

    Ví dụ Multi-Domain:
    - "Câu hỏi nào sau đây là đúng về chẩn đoán và điều trị trầm cảm?"
    → Đây là câu hỏi kiến thức về tâm thần học / y khoa, không yêu cầu hướng dẫn tự hại → gán Multi-Domain.

    -----------------------------------------------------

    YÊU CẦU BẮT BUỘC:
    - KHÔNG trả lời nội dung câu hỏi.
    - CHỈ trả về DUY NHẤT một mảng JSON.
    - Mảng JSON phải chứa CHÍNH XÁC số lượng câu hỏi trong user prompt (10 câu).
    - Mỗi phần tử có dạng:

    {
    "qid": "<mã câu hỏi>",
    "label": "<Precision-Critical|Compulsory|RAG|STEM|Multi-Domain>"
    }

    Ví dụ hợp lệ:
    [
    {"qid": "q1", "label": "RAG"},
    {"qid": "q2", "label": "STEM"},
    {"qid": "q3", "label": "Compulsory"}
    ]

    Không được trả về bất kỳ văn bản nào ngoài mảng JSON.
    '''
    user_prompt = f'''
        Danh sách các câu hỏi cần phân loại:
        {question_str}
        '''
        # 4. Cấu hình Request
    headers = { 
            'Authorization': model["authorization"], 
            'Token-id': model["tokenId"], 
            'Token-key': model["tokenKey"], 
            'Content-Type': 'application/json', 
        }

    json_data = {
            'model': 'vnptai_hackathon_small', 
            'messages': [
                {'role': 'system', 'content': system_prompt},
                {'role': 'user', 'content': user_prompt},
            ],
            'temperature': 0.0, 
            'top_p': 1.0, 
            'top_k': 0, 
            'n': 1, 
            'max_completion_tokens': 512
        }
    endpoint = "/v1/chat/completions/vnptai-hackathon-small"
    response = requests.post(f'https://api.idg.vnpt.vn/data-service{endpoint}', headers=headers, json=json_data) 
    response_js = response.json()
    result = json.loads(response_js["choices"][0]["message"]["content"])
    return result


def classify(data_path, model_name):
    """
    Args:
        data_path (_str_): Path to dataset need classifying
        model_name (_str_): Name of VNPT model that you want to use

    Returns:
        list(_json-object_): Dataset is already joined with label for each item
    """
    vnpt_model = get_api_entry_by_llm(model_name) 
    data = get_data(data_path)

    BATCH_SIZE_CLASSIFY = 20
    classified_results = []
    for i in range(0,len(data),BATCH_SIZE_CLASSIFY):
        if i+BATCH_SIZE_CLASSIFY>len(data):
            result = question_classify(data[i:len(data)], vnpt_model)
            classified_results.extend(result)
        else:
            result = question_classify(data[i:(i+BATCH_SIZE_CLASSIFY)], vnpt_model)
            classified_results.extend(result)


    classified_data = merge_by_qid(data,classified_results)
    return classified_data