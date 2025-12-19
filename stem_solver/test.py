from stem_solver.infer import run_stem_infer, solve_stem_question

if __name__ == "__main__":
    # run_stem_infer(
    #     input_path="STEM.json",
    #     output_path="test.csv",
    #     mode='strict'
    #     )
    
    
    test =     {
        "qid": "test_0194",
        "question": "Một dây dẫn thẳng dài mang dòng điện $ I $ và được bao quanh bởi một lớp vỏ trụ bán kính $ R $ với mật độ dòng điện đều $ J $ chảy theo hướng ngược lại. Lớp vỏ không dẫn điện. Tại khoảng cách $ r $ từ dây dẫn, với $ R < r $, độ lớn của từ trường $ B $ là bao nhiêu?",
        "choices": [
            "$ \\frac{\\mu_0 I}{2 \\pi r} $",
            "$ \\frac{\\mu_0 I}{2 \\pi R} $",
            "$ \\frac{\\mu_0 J R^2}{2 \\pi r^2} $",
            "$ \\frac{\\mu_0 J R^2}{2 \\pi R} $",
            "$ \\frac{\\mu_0 (I - J \\pi R^2)}{2 \\pi r} $",
            "$ \\frac{\\mu_0 (I - J \\pi r^2)}{2 \\pi r} $",
            "$ \\frac{\\mu_0 (I - J \\pi R^2)}{2 \\pi R} $",
            "$ \\frac{\\mu_0 (I - J \\pi r^2)}{2 \\pi R} $",
            "$ \\frac{\\mu_0 (I + J \\pi R^2)}{2 \\pi r} $",
            "$ \\frac{\\mu_0 (I + J \\pi r^2)}{2 \\pi r} $"
        ]
    }
    
    print(solve_stem_question(test["question"], test["choices"]))
    