# 导入所需的库
from selenium import webdriver  # 用于控制浏览器
from selenium.webdriver.common.by import By  # 用于定位网页元素
from selenium.webdriver.support.ui import WebDriverWait  # 用于等待网页元素加载
from selenium.webdriver.support import expected_conditions as EC  # 用于设置等待条件
from selenium.webdriver.edge.service import Service  # 用于设置Edge浏览器驱动
from http import HTTPStatus  # 用于处理HTTP状态码
import dashscope  # 阿里云API
from dashscope import Generation  # 阿里云生成模型
import random  # 用于生成随机数
import time  # 用于添加延时
import json  # 用于处理JSON数据

class AutoExam:
    def __init__(self):
        """
        初始化自动答题类
        设置浏览器驱动并创建浏览器实例
        """
        # 创建Edge浏览器驱动服务
        service = Service('D:/python/msedgedriver.exe')
        # 创建浏览器实例
        self.driver = webdriver.Edge(service=service)
        # 创建等待对象，最长等待时间为10秒
        self.wait = WebDriverWait(self.driver, 10)
        # 创建阿里云API实例
        self.dsapi = DashScopeAPI()

    def start_exam(self):
        """
        开始考试：
        1. 打开指定网址
        2. 等待页面加载
        3. 点击"顺序练习"链接
        """
        try:
            # 打开指定网址
            self.driver.get("https://www.jsyks.com/")
            # 等待页面完全加载
            time.sleep(3)
            
            # 只使用一种最可靠的定位方式
            practice_link = self.wait.until(
                EC.presence_of_element_located((By.XPATH, "//a[.//img[@alt='科目一顺序练习']]"))
            )
            
            # 使用JavaScript点击元素，避免被遮挡的问题
            self.driver.execute_script("arguments[0].scrollIntoView(true);", practice_link)
            time.sleep(1)  # 等待滚动完成
            self.driver.execute_script("arguments[0].click();", practice_link)
            
            # 等待新页面加载
            time.sleep(3)
            
            # 切换到新打开的标签页
            self.driver.switch_to.window(self.driver.window_handles[-1])
            
            # 等待题目页面加载完成
            self.wait.until(
                EC.presence_of_element_located((By.ID, "ExamTit"))
            )
            
        except Exception as e:
            print(f"启动考试时出错: {e}")
            print("具体错误：无法找到或点击'顺序练习'链接")
            # 如果发生错误，尝试关闭浏览器
            self.driver.quit()
            raise  # 重新抛出异常，中止程序

    def get_question_content(self):
        """
        获取题目内容
        返回值：题目文本，如果出错返回None
        """
        try:
            # 增加重试机制
            for _ in range(3):  # 最多重试3次
                try:
                    # 等待题目元素出现并获取文本
                    question_element = self.wait.until(
                        EC.visibility_of_element_located((By.ID, "ExamTit"))
                    )
                    # 获取题目文本并清理多余的空格和特殊字符
                    question_text = question_element.text.replace('\u00A0', ' ').strip()
                    if question_text:  # 确保获取到了文本
                        print("\n获取到的题目：")
                        print(question_text)
                        return question_text
                    time.sleep(1)
                except:
                    time.sleep(1)
            raise Exception("无法获取题目内容")
        except Exception as e:
            print(f"获取题目时出错: {e}")
            return None

    def get_options(self):
        """
        获取所有选项内容
        返回值：选项文本列表，如果出错返回None
        """
        try:
            # 增加重试机制
            for _ in range(3):  # 最多重试3次
                try:
                    # 等待选项列表元素出现
                    options_list = self.wait.until(
                        EC.visibility_of_element_located((By.ID, "ExamOpt"))
                    )
                    
                    options = []
                    # 遍历选项A到D
                    for option_id in ['ExamOptA', 'ExamOptB', 'ExamOptC', 'ExamOptD']:
                        option_element = self.wait.until(
                            EC.visibility_of_element_located((By.ID, option_id))
                        )
                        # 获取label元素中的文本
                        label_text = option_element.find_element(By.TAG_NAME, "label").text
                        if label_text:  # 确保获取到了文本
                            options.append(label_text)
                    
                    if len(options) == 4:  # 确保获取到了所有选项
                        print("\n获取到的选项：")
                        for i, option in enumerate(options):
                            print(f"{chr(65+i)}. {option}")  # 打印 A. xxx, B. xxx 等
                        return options
                    time.sleep(1)
                except:
                    time.sleep(1)
            raise Exception("无法获取完整的选项内容")
        except Exception as e:
            print(f"获取选项时出错: {e}")
            return None

    def choose_answer(self, answer):
        """
        选择答案
        参数：
            answer: AI返回的答案文本
        """
        try:
            # 从AI答案中提取选项字母（A、B、C、D）
            # 处理可能的答案格式：'B' 或 'B、12个月' 或 'B.'等
            answer = answer.strip().upper()  # 转换为大写并去除空格
            option_letter = answer[0]  # 获取第一个字符
            
            # 验证是否是有效的选项
            if option_letter not in ['A', 'B', 'C', 'D']:
                print(f"无效的答案格式: {answer}")
                return
            
            option_id = f"in{option_letter}"  # 构造选项ID，例如"inA"
            
            # 找到对应的单选按钮并点击
            answer_element = self.wait.until(
                EC.element_to_be_clickable((By.ID, option_id))
            )
            # 使用JavaScript点击元素，避免可能的点击问题
            self.driver.execute_script("arguments[0].click();", answer_element)
            print(f"已选择答案: {option_letter}")
            
        except Exception as e:
            print(f"选择答案时出错: {e}")
            print(f"尝试选择的答案选项: {answer}")

    def submit_to_ai(self, question, options):
        """
        将题目提交给AI获取答案
        参数：
            question: 题目文本
            options: 选项列表
        返回值：AI的答案
        """
        # 将题目和选项组合成完整的问题
        full_question = f"{question}\n" + "\n".join(options)
        # 构造发送给AI的消息，强调只需要返回选项字母
        messages = [
            {'role': 'system', 'content': 'You are a helpful assistant. Please only respond with a single letter (A, B, C, or D) as the answer.'},
            {'role': 'user', 'content': f'请只回答选项字母（A、B、C、D），不要包含其他内容。题目：{full_question}'}
        ]
        # 调用AI获取答案
        answer = self.dsapi.call_with_messages(messages)
        if answer:
            print("\nAI的答案：")
            print(answer)
        return answer

    def click_next_question(self):
        """
        点击下一题按钮
        返回值：是否成功点击下一题
        """
        try:
            # 通过span标签文本定位"下一题"按钮
            next_button = self.wait.until(
                EC.element_to_be_clickable((By.XPATH, "//span[text()='下一题']"))
            )
            next_button.click()
            time.sleep(2)  # 等待新题目加载
            return True
        except Exception as e:
            print(f"点击下一题时出错: {e}")
            return False

    def run(self):
        """
        运行主程序
        控制答题流程 - 循环处理题目直到用户选择退出
        """
        try:
            # 开始考试
            self.start_exam()
            
            question_count = 0
            while True:
                question_count += 1
                print(f"\n正在处理第 {question_count} 题...")
                
                # 获取题目内容
                question = self.get_question_content()
                # 获取选项内容
                options = self.get_options()
                
                # 如果成功获取到题目和选项
                if question and options:
                    # 获取AI答案
                    ai_answer = self.submit_to_ai(question, options)
                    # 选择答案
                    self.choose_answer(ai_answer)
                    print(f"\n第 {question_count} 题完成！")
                    
                    # 询问用户是否继续下一题
                    user_input = input("\n是否继续下一题？(y/n): ").lower()
                    if user_input != 'y':
                        print("\n答题结束！")
                        break
                    
                    # 点击下一题
                    if not self.click_next_question():
                        print("\n无法进入下一题，答题结束！")
                        break
                else:
                    print("\n获取题目或选项失败！")
                    break
                
        except Exception as e:
            print(f"运行出错: {e}")
        finally:
            # 等待用户按键后关闭浏览器
            input("\n按回车键关闭浏览器...")
            self.driver.quit()

# 保持原有的DashScopeAPI类不变
class DashScopeAPI:
    def __init__(self):
        dashscope.api_key = "sk-f02484ea78744f5a90a6b680bc288dbb"
    
    def call_with_messages(self, messages):
        response = Generation.call(
            model="qwen-turbo",
            messages=messages,
            seed=random.randint(1, 10000),
            result_format='message'
        )
        if response.status_code == HTTPStatus.OK:
            return response.output.choices[0]['message']['content']
        else:
            print('Request id: %s, Status code: %s, error code: %s, error message: %s' % (
                response.request_id, response.status_code,
                response.code, response.message
            ))
            return None

# 程序入口
if __name__ == "__main__":
    # 创建自动答题实例并运行
    bot = AutoExam()
    bot.run() 