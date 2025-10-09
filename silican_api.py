import requests
import base64
import json
import time

def retry_on_failure(max_retries=3, delay=2):
    """重试装饰器"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except (requests.exceptions.Timeout, requests.exceptions.ConnectionError) as e:
                    if attempt == max_retries - 1:
                        return f"API调用失败，已重试{max_retries}次: {str(e)}"
                    print(f"第{attempt + 1}次尝试失败，{delay}秒后重试...")
                    time.sleep(delay)
                except Exception as e:
                    return f"调用失败: {str(e)}"
            return "API调用失败"
        return wrapper
    return decorator

class SilicanAPI:
    def __init__(self, api_key):
        self.api_key = api_key
        self.base_url = "https://api.siliconflow.cn/v1"  
    
    @retry_on_failure(max_retries=2, delay=3)
    def analyze_image(self, image_path, prompt):
        """调用硅基流动API分析图像"""
    # 读取并编码图像
        with open(image_path, "rb") as image_file:
            encoded_image = base64.b64encode(image_file.read()).decode('utf-8')
    
    # 构建请求
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
    
   
        payload = {
            "model": "Qwen/Qwen2.5-VL-72B-Instruct",  
            "messages": [
                {
                    "role": "user",
                    "content": [
                
                        {"type": "image_url", 
                        "image_url": {"url": f"data:image/jpeg;base64,{encoded_image}"}},
                        {"type": "text", "text": prompt}
                    ]
                }
            ],
            "max_tokens": 1000
    }
    
        try:
            response = requests.post(
                f"{self.base_url}/chat/completions", 
                headers=headers, 
                json=payload,
                timeout=60  # 设置60秒超时
            )
            response.raise_for_status()  # 触发HTTP错误
            return response.json()["choices"][0]["message"]["content"]
        except requests.exceptions.Timeout:
            return "API调用超时，请检查网络连接后重试"
        except requests.exceptions.HTTPError as e:
            # 打印详细错误信息以便调试
            return f"API错误 {response.status_code}: {response.text}"
        except requests.exceptions.ConnectionError:
            return "网络连接失败，请检查网络连接"
        except Exception as e:
            return f"调用失败: {str(e)}"
    
    def detect_crop_health(self, image_path):
        """检测农作物健康状态 """
    # 使用更精确的提示词获取综合评估
        comprehensive_prompt = """请作为农业专家分析这张农作物图片，提供以下结构化信息：
    1. 作物类型识别
    2. 健康状况评估（健康/不健康）
    3. 健康评分（0-100分，100为完全健康）
    4. 主要问题描述（如无问题则写"无"）
    5. 可能病因分析（如无问题则写"无"）
    
    请严格按照以下JSON格式回复，不要添加任何额外内容：
    {
        "crop_type": "作物类型",
        "health_status": "健康/不健康",
        "health_score": 0-100的整数,
        "main_issues": "问题描述",
        "possible_causes": "可能病因"
    }"""
    
    # 获取结构化分析结果
        analysis_result = self.analyze_image(image_path, comprehensive_prompt)
    
    # 尝试解析JSON响应
        try:
        # 提取JSON部分（模型可能会在JSON前后添加额外文本）
            import re
            json_match = re.search(r'\{.*\}', analysis_result, re.DOTALL)
            if json_match:
                result_data = json.loads(json_match.group())
            else:
            # 如果无法提取JSON，使用默认值
                result_data = {
                    "crop_type": "未知作物",
                    "health_status": "未知",
                    "health_score": 50,
                    "main_issues": "无法解析分析结果",
                    "possible_causes": "无法解析分析结果"
            }
        except json.JSONDecodeError:
        # JSON解析失败时的备用方案
            result_data = {
                "crop_type": "未知作物",
                "health_status": "未知",
                "health_score": 50,
                "main_issues": "无法解析分析结果",
                "possible_causes": "无法解析分析结果"
        }
    
        # 获取详细描述
        description_prompt = "请详细描述这张图片中的农作物状况，包括作物类型、叶片颜色、纹理、是否有斑点、虫害或其他异常区域。"
        description = self.analyze_image(image_path, description_prompt)
    
        # 获取防治建议
        suggestion_prompt = f"""根据以下作物状况提供具体的防治建议和管理措施：
        作物类型: {result_data["crop_type"]}
        健康状况: {result_data["health_status"]}
        主要问题: {result_data["main_issues"]}
        可能病因: {result_data["possible_causes"]}
    
        请提供详细、实用的建议："""
        suggestions = self.analyze_image(image_path, suggestion_prompt)
    
    # 基于健康评分确定健康状态和置信度
        health_score = result_data.get("health_score", 50)
        if health_score >= 80:
            health_status = "健康"
            confidence = health_score / 100.0
        elif health_score >= 50:
            health_status = "一般"
            confidence = health_score / 100.0 * 0.8  # 中等健康状态置信度略低
        else:
            health_status = "不健康"
            confidence = (100 - health_score) / 100.0  # 低分时对不健康状态更确信
    
    # 整合详细描述
        full_description = f"{description}\n\n专家分析:\n- 健康评分: {health_score}/100\n- 主要问题: {result_data['main_issues']}\n- 可能病因: {result_data['possible_causes']}"
    
        return {
            "crop_type": result_data["crop_type"],
            "health_status": health_status,
            "confidence": confidence,
            "health_score": health_score,
            "description": full_description,
            "suggestions": suggestions,
            "main_issues": result_data["main_issues"],
            "possible_causes": result_data["possible_causes"]
    }
    @retry_on_failure(max_retries=2, delay=3)
    def agricultural_qa(self, question):
        """农业知识问答"""
        prompt = f"""你是一名农业专家，请用中文回答以下农业相关问题。回答要详细、实用，适合农民朋友理解，非农业相关的问题请拒绝回答。

    问题：{question}

    请提供专业、准确的农业知识解答："""
    
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
    
        payload = {
            "model": "Qwen/Qwen2.5-72B-Instruct", 
            "messages": [
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            "max_tokens": 2000,
            "temperature": 0.7
        }
    
        try:
            response = requests.post(
                f"{self.base_url}/chat/completions", 
                headers=headers, 
                json=payload,
                timeout=60  # 添加超时设置
            )
            response.raise_for_status()
            result = response.json()
            return result["choices"][0]["message"]["content"]
        except requests.exceptions.Timeout:
            return "API调用超时，请检查网络连接后重试"
        except requests.exceptions.ConnectionError:
            return "网络连接失败，请检查网络连接"
        except requests.exceptions.RequestException as e:
            return f"网络请求失败: {str(e)}"
        except KeyError as e:
            return f"解析API响应失败: {str(e)}，响应内容: {response.text}"
        except Exception as e:
            return f"问答失败: {str(e)}"
    # 在SilicanAPI类中添加新方法
    @retry_on_failure(max_retries=2, delay=3)
    def generate_planting_advice(self, crop_type, prompt=None):
        """生成作物种植建议"""
        if prompt is None:
            prompt = f"""请为{crop_type}提供详细的种植计划，包括以下内容：
        1. 播种时间和方法
        2. 施肥时间和肥料类型
        3. 浇水时间和水量要求
        4. 病虫害防治时间和方法
        5. 收获时间和方法
        请按时间顺序列出关键农事活动。"""
    
        headers = {
        "Authorization": f"Bearer {self.api_key}",
        "Content-Type": "application/json"
    }
    
        payload = {
        "model": "Qwen/Qwen2.5-72B-Instruct", 
        "messages": [
            {
                "role": "user",
                "content": prompt
            }
        ],
        "max_tokens": 2000,
        "temperature": 0.7
    }
    
        try:
            response = requests.post(
                f"{self.base_url}/chat/completions", 
                headers=headers, 
                json=payload,
                timeout=60
            )
            response.raise_for_status()
            result = response.json()
            return result["choices"][0]["message"]["content"]
        except requests.exceptions.Timeout:
            return "API调用超时，请检查网络连接后重试"
        except requests.exceptions.ConnectionError:
            return "网络连接失败，请检查网络连接"
        except Exception as e:
            return f"生成种植建议失败: {str(e)}"

    def extract_events_from_advice(self, advice_text):
        """从建议文本中提取关键事件"""
        prompt = f"""请从以下农业建议中提取关键农事活动事件，并为每个事件标注时间参考和重要性(高/中/低)。
        输出格式要求为JSON列表，每个元素包含:
        - activity: 活动描述
        - time_reference: 时间参考(如:播种后10天, 3月中旬等)
        - importance: 重要性(高/中/低)
    
        农业建议文本:
        {advice_text}
    
        请只返回JSON格式的数据，不要其他内容。"""
    
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
    }
    
        payload = {
            "model": "Qwen/Qwen2.5-72B-Instruct", 
            "messages": [
            {
                "role": "user",
                "content": prompt
            }
        ],
            "max_tokens": 2000,
            "temperature": 0.3 
    }
    
        try:
            response = requests.post(
                f"{self.base_url}/chat/completions", 
                headers=headers, 
                json=payload,
                timeout=60
            )
            response.raise_for_status()
            result = response.json()
        
            # 尝试从响应中提取JSON
            import re
            json_match = re.search(r'\[.*\]', result["choices"][0]["message"]["content"], re.DOTALL)
            if json_match:
                import json
                return json.loads(json_match.group())
            else:
                # 如果无法提取JSON，返回空列表
                return []
            
        except requests.exceptions.Timeout:
            print("API调用超时，请检查网络连接后重试")
            return []
        except requests.exceptions.ConnectionError:
            print("网络连接失败，请检查网络连接")
            return []
        except Exception as e:
            print(f"提取事件失败: {str(e)}")
            return []

