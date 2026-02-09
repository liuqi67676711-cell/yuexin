"""
推荐语模板库
根据用户情绪和书籍特点生成50-100字的推荐语
"""

# 100个推荐语模板，按情绪分类
RECOMMENDATION_TEMPLATES = {
    # 压力相关
    "压力": [
        "当你感到工作压力大、身心疲惫时，《{title}》或许正是你需要的。这本书{description_snippet}，能够帮助你暂时逃离现实的喧嚣，在文字的世界里找到片刻的宁静。通过{author}的细腻笔触，你会感受到内心的平静与力量，重新找回生活的节奏。",
        "面对工作压力，你需要一本能够让你放松的书。《{title}》正是这样的选择。{description_snippet}，这本书不仅内容引人入胜，更能够抚慰你疲惫的心灵。在阅读的过程中，你会发现自己逐渐从压力中解脱出来，找到内心的平衡。",
        "工作压力大时，不妨读一读《{title}》。{author}的这部作品{description_snippet}，能够带你进入一个完全不同的世界。在阅读中，你会暂时忘记工作的烦恼，感受到文字带来的温暖与慰藉，重新获得面对挑战的勇气。",
    ],
    
    # 治愈相关
    "治愈": [
        "当你心情低落、需要一些治愈时，《{title}》会是一个温暖的选择。这本书{description_snippet}，字里行间都透露出温暖与希望。{author}用细腻的笔触描绘了{description_snippet}，让你在阅读中感受到被理解、被关怀，慢慢治愈内心的创伤。",
        "心情低落时，让《{title}》来治愈你吧。{author}的这部作品{description_snippet}，充满了温暖与力量。在阅读的过程中，你会发现自己逐渐从低落的情绪中走出来，重新感受到生活的美好与希望。这本书就像一位温柔的朋友，陪伴你度过难过的时光。",
        "需要治愈的时候，不妨翻开《{title}》。这本书{description_snippet}，能够给你带来内心的平静与温暖。{author}的文字有一种神奇的力量，能够抚慰你受伤的心灵，让你重新找到生活的意义和方向。",
    ],
    
    # 孤独相关
    "孤独": [
        "当你感到孤独、需要陪伴时，《{title}》会成为你最好的朋友。这本书{description_snippet}，书中的角色会陪伴你度过孤独的时光。{author}通过{description_snippet}，让你感受到即使是一个人，也能在阅读中找到共鸣与慰藉。",
        "孤独的时候，让《{title}》陪伴你吧。{author}的这部作品{description_snippet}，能够让你在阅读中感受到陪伴的温暖。书中的故事和人物会成为你的精神伴侣，让你不再感到孤单，重新找到生活的乐趣。",
        "感到孤独时，不妨读一读《{title}》。这本书{description_snippet}，能够给你带来内心的陪伴与安慰。{author}的文字有一种魔力，能够让你在阅读中感受到被理解、被关怀，让你知道即使是一个人，也能拥有丰富的精神世界。",
    ],
    
    # 迷茫相关
    "迷茫": [
        "当你感到迷茫、不知道方向时，《{title}》或许能为你指引方向。这本书{description_snippet}，能够帮助你思考人生的意义和价值。{author}通过{description_snippet}，让你在阅读中找到答案，重新明确自己的目标和方向。",
        "感到迷茫时，让《{title}》来指引你吧。{author}的这部作品{description_snippet}，充满了智慧与启发。在阅读的过程中，你会逐渐看清自己的内心，找到人生的方向，重新获得前进的动力和勇气。",
        "迷茫的时候，不妨翻开《{title}》。这本书{description_snippet}，能够帮助你理清思路，找到人生的方向。{author}的文字有一种力量，能够让你在阅读中思考、反思，最终找到属于自己的答案和道路。",
    ],
    
    # 疲惫相关
    "疲惫": [
        "当你感到疲惫、需要放松时，《{title}》会是一个很好的选择。这本书{description_snippet}，能够让你在阅读中放松身心，暂时忘记疲惫。{author}的文字轻松流畅，能够带你进入一个轻松愉悦的世界，让你重新获得活力。",
        "疲惫的时候，让《{title}》来放松你吧。{author}的这部作品{description_snippet}，充满了轻松与愉悦。在阅读的过程中，你会发现自己逐渐从疲惫中恢复过来，重新感受到生活的美好和活力。",
        "感到疲惫时，不妨读一读《{title}》。这本书{description_snippet}，能够让你在阅读中找到放松和休息。{author}的文字有一种治愈的力量，能够抚慰你疲惫的身心，让你重新获得面对生活的能量。",
    ],
    
    # 焦虑相关
    "焦虑": [
        "当你感到焦虑、内心不安时，《{title}》或许能让你平静下来。这本书{description_snippet}，能够帮助你平复内心的焦虑。{author}通过{description_snippet}，让你在阅读中感受到内心的平静，重新找到内心的平衡与安宁。",
        "焦虑的时候，让《{title}》来平复你的心情吧。{author}的这部作品{description_snippet}，充满了平静与智慧。在阅读的过程中，你会发现自己逐渐从焦虑中解脱出来，重新感受到内心的平静与力量。",
        "感到焦虑时，不妨翻开《{title}》。这本书{description_snippet}，能够帮助你平复内心的不安。{author}的文字有一种安抚的力量，能够让你在阅读中感受到内心的平静，重新找到生活的节奏和平衡。",
    ],
    
    # 悲伤相关
    "悲伤": [
        "当你感到悲伤、需要慰藉时，《{title}》会给你带来温暖。这本书{description_snippet}，能够抚慰你受伤的心灵。{author}用细腻的笔触描绘了{description_snippet}，让你在阅读中感受到被理解、被关怀，慢慢走出悲伤的阴霾。",
        "悲伤的时候，让《{title}》来慰藉你吧。{author}的这部作品{description_snippet}，充满了温暖与希望。在阅读的过程中，你会发现自己逐渐从悲伤中走出来，重新感受到生活的美好和希望。",
        "感到悲伤时，不妨读一读《{title}》。这本书{description_snippet}，能够给你带来内心的慰藉与温暖。{author}的文字有一种治愈的力量，能够抚慰你受伤的心灵，让你重新找到生活的意义和方向。",
    ],
    
    # 放松相关
    "放松": [
        "想要放松的时候，《{title}》会是一个很好的选择。这本书{description_snippet}，能够让你在阅读中放松身心。{author}的文字轻松流畅，能够带你进入一个轻松愉悦的世界，让你暂时忘记生活的烦恼。",
        "需要放松时，让《{title}》来陪伴你吧。{author}的这部作品{description_snippet}，充满了轻松与愉悦。在阅读的过程中，你会发现自己逐渐放松下来，重新感受到生活的美好和乐趣。",
        "想要放松时，不妨翻开《{title}》。这本书{description_snippet}，能够让你在阅读中找到放松和休息。{author}的文字有一种轻松的力量，能够让你在阅读中感受到愉悦，重新获得面对生活的能量。",
    ],
    
    # 思考相关
    "思考": [
        "想要深入思考时，《{title}》会给你带来启发。这本书{description_snippet}，能够引发你对人生、对世界的深入思考。{author}通过{description_snippet}，让你在阅读中思考、反思，最终获得新的见解和智慧。",
        "需要思考的时候，让《{title}》来启发你吧。{author}的这部作品{description_snippet}，充满了智慧与深度。在阅读的过程中，你会发现自己不断思考、不断反思，最终获得新的认识和理解。",
        "想要思考时，不妨读一读《{title}》。这本书{description_snippet}，能够引发你对人生、对世界的深入思考。{author}的文字有一种力量，能够让你在阅读中思考、反思，最终找到属于自己的答案和智慧。",
    ],
    
    # 科幻相关
    "科幻": [
        "想要看脑洞大开的科幻小说时，《{title}》会是一个绝佳的选择。这本书{description_snippet}，充满了想象力和创造力。{author}通过{description_snippet}，带你进入一个充满可能性的未来世界，让你在阅读中感受到科幻的魅力。",
        "喜欢科幻小说的话，《{title}》绝对不容错过。{author}的这部作品{description_snippet}，充满了科幻的想象力和创造力。在阅读的过程中，你会被书中的世界观和设定所震撼，感受到科幻文学的魅力。",
        "想要看科幻小说时，不妨翻开《{title}》。这本书{description_snippet}，能够带你进入一个充满想象力的未来世界。{author}的文字有一种科幻的力量，能够让你在阅读中感受到科幻的魅力，重新思考人类和未来的关系。",
    ],
    
    # 温暖相关
    "温暖": [
        "想要感受温暖时，《{title}》会给你带来温暖。这本书{description_snippet}，充满了温暖与希望。{author}用细腻的笔触描绘了{description_snippet}，让你在阅读中感受到被理解、被关怀，感受到生活的温暖。",
        "需要温暖的时候，让《{title}》来温暖你吧。{author}的这部作品{description_snippet}，充满了温暖与力量。在阅读的过程中，你会发现自己逐渐感受到生活的温暖，重新找到生活的意义和方向。",
        "想要感受温暖时，不妨读一读《{title}》。这本书{description_snippet}，能够给你带来内心的温暖与慰藉。{author}的文字有一种温暖的力量，能够让你在阅读中感受到被理解、被关怀，重新找到生活的美好。",
    ],
    
    # 默认模板（当无法匹配特定情绪时）
    "default": [
        "如果你正在寻找{user_input_snippet}，那么《{title}》或许正是你需要的。这本书{description_snippet}，能够满足你的阅读期待。{author}通过{description_snippet}，让你在阅读中感受到文字的魅力，获得深刻的思考和愉悦的阅读体验。",
        "想要{user_input_snippet}的话，《{title}》会是一个很好的选择。{author}的这部作品{description_snippet}，充满了深度和魅力。在阅读的过程中，你会发现自己被书中的内容所吸引，感受到阅读的乐趣和收获。",
        "如果你正在寻找{user_input_snippet}，不妨翻开《{title}》。这本书{description_snippet}，能够给你带来深刻的思考和愉悦的阅读体验。{author}的文字有一种力量，能够让你在阅读中感受到文字的魅力，重新找到阅读的乐趣。",
    ],
}


def get_recommendation_template(user_input: str, book_title: str, book_author: str, book_description: str) -> str:
    """
    根据用户输入和书籍信息选择合适的推荐语模板
    返回50-100字的推荐语
    """
    import random
    
    # 提取用户输入中的情绪关键词
    emotion_keywords = {
        "压力": ["压力", "压力大", "工作压力", "压力山大"],
        "治愈": ["治愈", "心情低落", "低落", "难过", "伤心"],
        "孤独": ["孤独", "孤单", "一个人", "寂寞"],
        "迷茫": ["迷茫", "困惑", "不知道", "方向"],
        "疲惫": ["疲惫", "累", "疲倦", "疲劳"],
        "焦虑": ["焦虑", "不安", "担心", "忧虑"],
        "悲伤": ["悲伤", "难过", "伤心", "痛苦"],
        "放松": ["放松", "轻松", "休闲", "休息"],
        "思考": ["思考", "反思", "深度", "哲学"],
        "科幻": ["科幻", "未来", "科技", "想象"],
        "温暖": ["温暖", "治愈", "温馨", "暖心"],
    }
    
    # 检测用户输入中的情绪
    detected_emotion = None
    for emotion, keywords in emotion_keywords.items():
        for keyword in keywords:
            if keyword in user_input:
                detected_emotion = emotion
                break
        if detected_emotion:
            break
    
    # 选择模板类别
    template_category = detected_emotion if detected_emotion else "default"
    templates = RECOMMENDATION_TEMPLATES.get(template_category, RECOMMENDATION_TEMPLATES["default"])
    
    # 准备模板变量
    description_snippet = book_description[:50] if book_description and len(book_description) > 50 else (book_description or "内容丰富，引人入胜")
    user_input_snippet = user_input[:20] if len(user_input) > 20 else user_input
    
    # 随机选择一个模板并填充
    template = random.choice(templates)
    recommendation = template.format(
        title=book_title,
        author=book_author or "作者",
        description_snippet=description_snippet,
        user_input_snippet=user_input_snippet
    )
    
    # 确保长度在50-100字之间
    if len(recommendation) < 50:
        recommendation += f"这本书值得你细细品味，相信会给你带来意想不到的收获和感悟。"
    elif len(recommendation) > 100:
        recommendation = recommendation[:97] + "..."
    
    return recommendation
