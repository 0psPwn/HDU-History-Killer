#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
历史复习软件 - Flask Web应用
包含随机答题、题目查询和错题本功能
"""

from flask import Flask, render_template, request, jsonify, session
import json
import random
import os

app = Flask(__name__)
app.secret_key = 'history_review_secret_key'

# 错题本文件名
WRONG_QUESTIONS_FILE = 'wrong_questions.json'

# 加载题目数据
def load_questions():
    """加载历史题目数据"""
    with open('历史选择题整理.json', 'r', encoding='utf-8') as f:
        return json.load(f)

# 加载错题本数据
def load_wrong_questions():
    """加载错题本数据"""
    if os.path.exists(WRONG_QUESTIONS_FILE):
        with open(WRONG_QUESTIONS_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return []

# 保存错题本数据
def save_wrong_questions(wrong_questions):
    """保存错题本数据到文件"""
    with open(WRONG_QUESTIONS_FILE, 'w', encoding='utf-8') as f:
        json.dump(wrong_questions, f, ensure_ascii=False, indent=4)

# 添加错题到错题本
def add_to_wrong_questions(question_id):
    """将指定ID的题目添加到错题本"""
    questions = load_questions()
    wrong_questions = load_wrong_questions()
    
    # 检查题目是否已在错题本中
    for wrong in wrong_questions:
        if wrong['id'] == question_id:
            return False  # 题目已存在
    
    # 找到题目并添加到错题本
    question = next(q for q in questions if q['id'] == question_id)
    wrong_questions.append(question)
    save_wrong_questions(wrong_questions)
    return True

# 从错题本中删除题目
def remove_from_wrong_questions(question_id):
    """从错题本中删除指定ID的题目"""
    wrong_questions = load_wrong_questions()
    wrong_questions = [q for q in wrong_questions if q['id'] != question_id]
    save_wrong_questions(wrong_questions)

@app.route('/')
def index():
    """主页"""
    return render_template('index.html')

@app.route('/chapters')
def chapters():
    """章节选择页面"""
    questions = load_questions()
    # 提取所有章节名称（去重）
    chapters = list(set(q['chapter'] for q in questions))
    chapters.sort()
    return render_template('chapters.html', chapters=chapters)

@app.route('/chapter/<chapter_name>', methods=['GET', 'POST'])
def chapter_quiz(chapter_name):
    """章节答题功能"""
    questions = load_questions()
    # 获取指定章节的所有题目
    chapter_questions = [q for q in questions if q['chapter'] == chapter_name]
    
    if request.method == 'POST':
        # 处理答题结果
        user_answers = request.form.to_dict()
        score = 0
        total = len(user_answers)
        wrong_questions = []
        
        for question_id, user_answer in user_answers.items():
            question_id = int(question_id)
            # 找到对应的题目
            question = next(q for q in chapter_questions if q['id'] == question_id)
            if user_answer.upper() == question['answer'].upper():
                score += 1
            else:
                # 记录错题信息
                wrong_questions.append({
                    'question': question,
                    'user_answer': user_answer.upper(),
                    'correct_answer': question['answer'].upper()
                })
                # 自动将错题添加到错题本
                add_to_wrong_questions(question_id)
        
        # 计算得分
        percentage = (score / total) * 100
        return render_template('quiz_result.html', 
                             score=score, 
                             total=total, 
                             percentage=round(percentage, 1),
                             wrong_questions=wrong_questions)
    else:
        # 随机排序题目
        random.shuffle(chapter_questions)
        session['chapter_questions'] = chapter_questions
        return render_template('quiz.html', 
                             questions=chapter_questions, 
                             chapter_name=chapter_name)

@app.route('/quiz', methods=['GET', 'POST'])
def quiz():
    """随机答题功能"""
    questions = load_questions()
    
    if request.method == 'POST':
        # 处理答题结果
        user_answers = request.form.to_dict()
        score = 0
        total = len(user_answers)
        wrong_questions = []
        
        for question_id, user_answer in user_answers.items():
            question_id = int(question_id)
            # 找到对应的题目
            question = next(q for q in questions if q['id'] == question_id)
            if user_answer.upper() == question['answer'].upper():
                score += 1
            else:
                # 记录错题信息
                wrong_questions.append({
                    'question': question,
                    'user_answer': user_answer.upper(),
                    'correct_answer': question['answer'].upper()
                })
                # 自动将错题添加到错题本
                add_to_wrong_questions(question_id)
        
        # 计算得分
        percentage = (score / total) * 100
        return render_template('quiz_result.html', 
                             score=score, 
                             total=total, 
                             percentage=round(percentage, 1),
                             wrong_questions=wrong_questions)
    else:
        # 随机选择10道题目
        random_questions = random.sample(questions, 10)
        session['quiz_questions'] = random_questions
        return render_template('quiz.html', questions=random_questions)

@app.route('/search', methods=['GET', 'POST'])
def search():
    """题目查询功能"""
    questions = load_questions()
    results = []
    
    if request.method == 'POST':
        keyword = request.form['keyword'].strip()
        if keyword:
            # 根据关键词查询题目
            results = [q for q in questions if keyword in q['question']]
    
    return render_template('search.html', 
                         results=results, 
                         keyword=request.form.get('keyword', ''))

@app.route('/api/questions', methods=['GET'])
def api_questions():
    """API接口：获取题目数据"""
    questions = load_questions()
    return jsonify(questions)

@app.route('/api/random/<int:count>', methods=['GET'])
def api_random(count):
    """API接口：获取随机题目"""
    questions = load_questions()
    random_questions = random.sample(questions, min(count, len(questions)))
    return jsonify(random_questions)

@app.route('/api/search/<keyword>', methods=['GET'])
def api_search(keyword):
    """API接口：查询题目"""
    questions = load_questions()
    results = [q for q in questions if keyword in q['question']]
    return jsonify(results)

@app.route('/wrong_questions')
def wrong_questions():
    """错题本页面"""
    wrong_questions_list = load_wrong_questions()
    return render_template('wrong_questions.html', wrong_questions=wrong_questions_list)

@app.route('/wrong_quiz', methods=['GET', 'POST'])
def wrong_quiz():
    """错题练习功能"""
    wrong_questions_list = load_wrong_questions()
    
    if not wrong_questions_list:
        return render_template('wrong_quiz.html', questions=[], no_questions=True)
    
    if request.method == 'POST':
        # 处理答题结果
        user_answers = request.form.to_dict()
        score = 0
        total = len(user_answers)
        wrong_questions_result = []
        
        for question_id, user_answer in user_answers.items():
            question_id = int(question_id)
            # 找到对应的题目
            question = next(q for q in wrong_questions_list if q['id'] == question_id)
            if user_answer.upper() == question['answer'].upper():
                score += 1
                # 答对后从错题本中删除该题目
                remove_from_wrong_questions(question_id)
            else:
                # 记录错题信息
                wrong_questions_result.append({
                    'question': question,
                    'user_answer': user_answer.upper(),
                    'correct_answer': question['answer'].upper()
                })
        
        # 计算得分
        percentage = (score / total) * 100
        return render_template('wrong_quiz_result.html', 
                             score=score, 
                             total=total, 
                             percentage=round(percentage, 1),
                             wrong_questions=wrong_questions_result)
    else:
        # 随机排序错题
        random.shuffle(wrong_questions_list)
        session['wrong_questions'] = wrong_questions_list
        return render_template('wrong_quiz.html', questions=wrong_questions_list)

@app.route('/api/add_wrong/<int:question_id>', methods=['POST'])
def api_add_wrong(question_id):
    """API接口：添加错题到错题本"""
    success = add_to_wrong_questions(question_id)
    return jsonify({'success': success, 'message': '添加成功' if success else '题目已存在'})

@app.route('/api/remove_wrong/<int:question_id>', methods=['POST'])
def api_remove_wrong(question_id):
    """API接口：从错题本中删除题目"""
    remove_from_wrong_questions(question_id)
    return jsonify({'success': True, 'message': '删除成功'})

@app.route('/api/wrong_questions', methods=['GET'])
def api_wrong_questions():
    """API接口：获取错题本数据"""
    wrong_questions_list = load_wrong_questions()
    return jsonify(wrong_questions_list)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
