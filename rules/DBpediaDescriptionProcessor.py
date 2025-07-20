# dbpediaDescriptionProcessor.py

import re
import requests
from typing import Optional, Tuple, Dict
from functools import lru_cache


class DBpediaDescriptionProcessor:
    """使用DBpedia进行实体描述处理的处理器"""

    # def __init__(self, session=None):
    #     self.session = session or requests.Session()
    #     self.lookup_url = "https://lookup.dbpedia.org/api/search"
    #     self.sparql_endpoint = "http://dbpedia.org/sparql"
    #     self.max_retries = 3
    #     self.timeout = 10

    def __init__(self, session=None):
        self.session = session or requests.Session()
        self.lookup_url = "https://lookup.dbpedia.org/api/search"
        self.sparql_endpoint = "http://dbpedia.org/sparql"
        self.max_retries = 3
        self.timeout = 10

        # 如果没有提供session，检查是否需要代理
        if session is None:
            try:
                # 测试直接连接
                test_response = requests.get("http://dbpedia.org", timeout=3)
                print("Direct connection to DBpedia successful")
            except:
                print("Direct connection failed, setting up proxy")
                self.session.proxies = {
                    "http": "http://127.0.0.1:7890",
                    "https": "http://127.0.0.1:7890",
                }

    # def get_entity_description(self, entity_text: str, entity_type: str, ner_model: str = "conll") -> str:
    #     """
    #     获取实体的简洁描述
    #
    #     Args:
    #         entity_text: 实体名称
    #         entity_type: 实体类型（原始NER标签）
    #         ner_model: NER模型类型 ("conll3", "ontonotes", "azure", "aws")
    #
    #     Returns:
    #         str: 格式化的简洁描述
    #     """
    #     try:
    #         # 标准化实体类型
    #         std_entity_type = self._standardize_entity_type(entity_type, ner_model)
    #         print(f"\nProcessing entity: {entity_text} ({entity_type} -> {std_entity_type}) [Model: {ner_model}]")
    #
    #         # 1. 先尝试链接到DBpedia URI
    #         entity_uri = self._link_entity(entity_text, std_entity_type)
    #
    #         if entity_uri:
    #             print(f"Found URI: {entity_uri}")
    #
    #             # 2. 尝试获取简短描述（使用SPARQL查询特定属性）
    #             short_description = self._get_short_description(entity_uri, std_entity_type)
    #             if short_description:
    #                 print(f"✓ Using DBpedia short description: {short_description}")
    #                 return short_description
    #
    #             # 3. 如果没有简短描述，从摘要中提取
    #             abstract = self._get_dbpedia_abstract(entity_uri)
    #             if abstract:
    #                 processed = self._extract_concise_description(abstract, entity_text, std_entity_type)
    #                 if processed:
    #                     print(f"✓ Using processed DBpedia description: {processed}")
    #                     return processed
    #
    #         # 4. 最后使用fallback
    #         fallback = self._get_fallback_description(entity_type, ner_model)
    #         print(f"! Using fallback description: {fallback}")
    #         return fallback
    #
    #     except Exception as e:
    #         print(f"✗ Error in description process: {e}")
    #         return self._get_fallback_description(entity_type, ner_model)

    # 修改 dbpediaDescriptionProcessor.py

    def get_entity_description(self, entity_text: str, entity_type: str, ner_model: str = "conll") -> str:
        """获取实体的简洁描述"""
        try:
            # 标准化实体类型
            std_entity_type = self._standardize_entity_type(entity_type, ner_model)
            print(f"\nProcessing entity: {entity_text} ({entity_type} -> {std_entity_type}) [Model: {ner_model}]")

            # 1. 先尝试链接到DBpedia URI
            entity_uri = self._link_entity(entity_text, std_entity_type)

            if entity_uri:
                print(f"Found URI: {entity_uri}")

                # 2. 尝试获取简短描述
                print(f"Attempting to get short description...")
                short_description = self._get_short_description(entity_uri, std_entity_type)
                if short_description:
                    print(f"✓ Using DBpedia short description: {short_description}")
                    return short_description
                else:
                    print(f"No short description found")

                # 3. 如果没有简短描述，从摘要中提取
                print(f"Attempting to get abstract...")
                abstract = self._get_dbpedia_abstract(entity_uri)
                if abstract:
                    print(f"Found abstract (length: {len(abstract)})")
                    processed = self._extract_concise_description(abstract, entity_text, std_entity_type)
                    if processed:
                        print(f"✓ Using processed DBpedia description: {processed}")
                        return processed
                    else:
                        print(f"Could not extract concise description from abstract")
                else:
                    print(f"No abstract found")

            # 4. 最后使用fallback
            fallback = self._get_fallback_description(entity_type, ner_model)
            print(f"! Using fallback description: {fallback}")
            return fallback

        except Exception as e:
            print(f"✗ Error in description process: {e}")
            import traceback
            traceback.print_exc()
            return self._get_fallback_description(entity_type, ner_model)

    def _standardize_entity_type(self, entity_type: str, ner_model: str) -> str:
        """将不同NER模型的实体类型标准化为通用类型"""

        if ner_model.lower() == "conll3":
            conll3_mapping = {
                "PER": "PERSON",
                "ORG": "ORGANIZATION",
                "LOC": "LOCATION",
                "MISC": "MISC"
            }
            return conll3_mapping.get(entity_type, "MISC")

        elif ner_model.lower() == "ontonotes":
            ontonotes_mapping = {
                "PERSON": "PERSON",
                "ORG": "ORGANIZATION",
                "GPE": "LOCATION",
                "LOC": "LOCATION",
                "FAC": "LOCATION",
                "EVENT": "EVENT",
                "WORK_OF_ART": "WORK_OF_ART",
                "PRODUCT": "PRODUCT",
                "NORP": "GROUP",
                "LANGUAGE": "MISC",
                "DATE": "DATE",
                "TIME": "TIME",
                "PERCENT": "QUANTITY",
                "MONEY": "QUANTITY",
                "QUANTITY": "QUANTITY",
                "ORDINAL": "QUANTITY",
                "CARDINAL": "QUANTITY",
                "LAW": "MISC"
            }
            return ontonotes_mapping.get(entity_type, "MISC")

        elif ner_model.lower() == "azure":
            azure_mapping = {
                "Person": "PERSON",
                "PersonType": "PERSON",
                "Location": "LOCATION",
                "Organization": "ORGANIZATION",
                "Event": "EVENT",
                "Product": "PRODUCT",
                "Skill": "MISC",
                "Address": "LOCATION",
                "PhoneNumber": "CONTACT",
                "Email": "CONTACT",
                "URL": "CONTACT",
                "IP": "CONTACT",
                "DateTime": "DATE",
                "Quantity": "QUANTITY"
            }
            return azure_mapping.get(entity_type, "MISC")

        elif ner_model.lower() == "aws":
            aws_mapping = {
                "PERSON": "PERSON",
                "LOCATION": "LOCATION",
                "ORGANIZATION": "ORGANIZATION",
                "COMMERCIAL_ITEM": "PRODUCT",
                "EVENT": "EVENT",
                "DATE": "DATE",
                "QUANTITY": "QUANTITY",
                "TITLE": "WORK_OF_ART",
                "OTHER": "MISC"
            }
            return aws_mapping.get(entity_type, "MISC")

        return entity_type

    @lru_cache(maxsize=200)
    def _link_entity(self, entity_text: str, std_entity_type: str) -> Optional[str]:
        """链接实体到DBpedia URI"""
        try:
            response = self.session.get(
                self.lookup_url,
                headers={'Accept': 'application/json'},
                params={
                    'query': entity_text,
                    'format': 'json',
                    'maxResults': 5
                },
                timeout=self.timeout
            )

            if response.status_code == 200:
                data = response.json()

                if "docs" in data and data["docs"]:
                    # 类型映射
                    type_mappings = {
                        "PERSON": ["http://dbpedia.org/ontology/Person"],
                        "ORGANIZATION": [
                            "http://dbpedia.org/ontology/Organisation",
                            "http://dbpedia.org/ontology/Company",
                            "http://dbpedia.org/ontology/Corporation"
                        ],
                        "LOCATION": [
                            "http://dbpedia.org/ontology/Place",
                            "http://dbpedia.org/ontology/Location",
                            "http://dbpedia.org/ontology/Country",
                            "http://dbpedia.org/ontology/City"
                        ],
                        "EVENT": [
                            "http://dbpedia.org/ontology/Event",
                            "http://dbpedia.org/ontology/SocietalEvent"
                        ],
                        "PRODUCT": [
                            "http://dbpedia.org/ontology/Product",
                            "http://dbpedia.org/ontology/Device"
                        ],
                        "WORK_OF_ART": [
                            "http://dbpedia.org/ontology/Work",
                            "http://dbpedia.org/ontology/Book",
                            "http://dbpedia.org/ontology/Film"
                        ]
                    }

                    desired_types = type_mappings.get(std_entity_type, [])

                    # 优先返回类型匹配的结果
                    for doc in data["docs"]:
                        if desired_types and any(t in doc.get("type", []) for t in desired_types):
                            return doc.get("resource", [None])[0]

                    # 如果没有类型匹配，返回第一个结果
                    return data["docs"][0].get("resource", [None])[0]

        except Exception as e:
            print(f"Entity linking failed: {e}")

        return None

    # @lru_cache(maxsize=200)
    # def _get_short_description(self, uri: str, std_entity_type: str) -> Optional[str]:
    #     """尝试获取简短描述（类似Wikidata的短描述）"""
    #     try:
    #         # 根据实体类型查询特定属性
    #         type_queries = {
    #             "PERSON": """
    #                 SELECT ?occupation ?nationality WHERE {
    #                     OPTIONAL { <{uri}> dbo:occupation ?occupation }
    #                     OPTIONAL { <{uri}> dbo:nationality ?nationality }
    #                 } LIMIT 1
    #             """,
    #             "ORGANIZATION": """
    #                 SELECT ?industry ?type WHERE {
    #                     OPTIONAL { <{uri}> dbo:industry ?industry }
    #                     OPTIONAL { <{uri}> dbo:type ?type }
    #                 } LIMIT 1
    #             """,
    #             "LOCATION": """
    #                 SELECT ?type ?country WHERE {
    #                     OPTIONAL { <{uri}> a ?type . FILTER(STRSTARTS(STR(?type), "http://dbpedia.org/ontology/")) }
    #                     OPTIONAL { <{uri}> dbo:country ?country }
    #                 } LIMIT 1
    #             """
    #         }
    #
    #         query_template = type_queries.get(std_entity_type, "")
    #         if not query_template:
    #             return None
    #
    #         query = f"""
    #         PREFIX dbo: <http://dbpedia.org/ontology/>
    #         {query_template.format(uri=uri)}
    #         """
    #
    #         response = self.session.get(
    #             self.sparql_endpoint,
    #             headers={
    #                 'Accept': 'application/sparql-results+json',
    #                 'User-Agent': 'Mozilla/5.0'
    #             },
    #             params={
    #                 'query': query,
    #                 'format': 'json'
    #             },
    #             timeout=self.timeout
    #         )
    #
    #         if response.status_code == 200:
    #             result = response.json()
    #             if result and result["results"]["bindings"]:
    #                 binding = result["results"]["bindings"][0]
    #
    #                 # 构建简短描述
    #                 if std_entity_type == "PERSON":
    #                     occupation = self._extract_last_part(binding.get("occupation", {}).get("value", ""))
    #                     nationality = self._extract_last_part(binding.get("nationality", {}).get("value", ""))
    #
    #                     if nationality and occupation:
    #                         return f"{uri.split('/')[-1].replace('_', ' ')} is a {nationality} {occupation}."
    #                     elif occupation:
    #                         return f"{uri.split('/')[-1].replace('_', ' ')} is a {occupation}."
    #
    #                 elif std_entity_type == "ORGANIZATION":
    #                     industry = self._extract_last_part(binding.get("industry", {}).get("value", ""))
    #                     if industry:
    #                         return f"{uri.split('/')[-1].replace('_', ' ')} is a {industry} company."
    #
    #                 elif std_entity_type == "LOCATION":
    #                     type_val = self._extract_last_part(binding.get("type", {}).get("value", ""))
    #                     if type_val and type_val.lower() != "thing":
    #                         return f"{uri.split('/')[-1].replace('_', ' ')} is a {type_val.lower()}."
    #
    #     except Exception as e:
    #         print(f"Short description query error: {e}")
    #
    #     return None

    @lru_cache(maxsize=200)
    def _get_short_description(self, uri: str, std_entity_type: str) -> Optional[str]:
        """尝试获取简短描述（类似Wikidata的短描述）"""
        try:
            # 根据实体类型构建查询
            if std_entity_type == "PERSON":
                query = f"""
                PREFIX dbo: <http://dbpedia.org/ontology/>
                SELECT ?occupation ?nationality WHERE {{
                    OPTIONAL {{ <{uri}> dbo:occupation ?occupation }}
                    OPTIONAL {{ <{uri}> dbo:nationality ?nationality }}
                }} LIMIT 1
                """
            elif std_entity_type == "ORGANIZATION":
                query = f"""
                PREFIX dbo: <http://dbpedia.org/ontology/>
                SELECT ?industry ?type WHERE {{
                    OPTIONAL {{ <{uri}> dbo:industry ?industry }}
                    OPTIONAL {{ <{uri}> dbo:type ?type }}
                }} LIMIT 1
                """
            elif std_entity_type == "LOCATION":
                query = f"""
                PREFIX dbo: <http://dbpedia.org/ontology/>
                SELECT ?type ?country WHERE {{
                    OPTIONAL {{ <{uri}> a ?type . FILTER(STRSTARTS(STR(?type), "http://dbpedia.org/ontology/")) }}
                    OPTIONAL {{ <{uri}> dbo:country ?country }}
                }} LIMIT 1
                """
            else:
                return None

            response = self.session.get(
                self.sparql_endpoint,
                headers={
                    'Accept': 'application/sparql-results+json',
                    'User-Agent': 'Mozilla/5.0'
                },
                params={
                    'query': query,
                    'format': 'json'
                },
                timeout=self.timeout
            )

            if response.status_code == 200:
                result = response.json()
                if result and result["results"]["bindings"]:
                    binding = result["results"]["bindings"][0]

                    # 提取实体名称
                    entity_name = uri.split('/')[-1].replace('_', ' ')

                    # 构建简短描述
                    if std_entity_type == "PERSON":
                        occupation = self._extract_last_part(binding.get("occupation", {}).get("value", ""))
                        nationality = self._extract_last_part(binding.get("nationality", {}).get("value", ""))

                        if nationality and occupation:
                            return f"{entity_name} is a {nationality} {occupation}."
                        elif occupation:
                            return f"{entity_name} is a {occupation}."

                    elif std_entity_type == "ORGANIZATION":
                        industry = self._extract_last_part(binding.get("industry", {}).get("value", ""))
                        if industry:
                            return f"{entity_name} is a {industry} company."

                    elif std_entity_type == "LOCATION":
                        type_val = self._extract_last_part(binding.get("type", {}).get("value", ""))
                        if type_val and type_val.lower() not in ["thing", "place"]:
                            return f"{entity_name} is a {type_val.lower()}."

        except Exception as e:
            print(f"Short description query error: {e}")

        return None

    @lru_cache(maxsize=200)
    def _get_dbpedia_abstract(self, uri: str) -> Optional[str]:
        """从DBpedia获取摘要"""
        try:
            query = f"""
            PREFIX dbo: <http://dbpedia.org/ontology/>

            SELECT ?abstract WHERE {{
                <{uri}> dbo:abstract ?abstract .
                FILTER(LANG(?abstract) = 'en')
            }}
            LIMIT 1
            """

            response = self.session.get(
                self.sparql_endpoint,
                headers={
                    'Accept': 'application/sparql-results+json',
                    'User-Agent': 'Mozilla/5.0'
                },
                params={
                    'query': query,
                    'format': 'json'
                },
                timeout=self.timeout
            )

            if response.status_code == 200:
                result = response.json()
                if result and result["results"]["bindings"]:
                    binding = result["results"]["bindings"][0]
                    return binding.get("abstract", {}).get("value", "")

        except Exception as e:
            print(f"Abstract query error: {e}")

        return None

    # def _extract_concise_description(self, abstract: str, entity_name: str, std_entity_type: str) -> str:
    #     """从摘要中提取最精简的描述"""
    #     if not abstract:
    #         return ""
    #
    #     # 清理文本
    #     cleaned = self._basic_cleaning(abstract)
    #
    #     # 提取第一句
    #     first_sentence = self._extract_first_sentence(cleaned)
    #     if not first_sentence:
    #         return ""
    #
    #     # 尝试提取"is a/an"模式
    #     is_pattern = re.search(
    #         r'(?:is|was)\s+(a|an)\s+([^,\.]{3,30})(?:[,\.]|$)',
    #         first_sentence,
    #         re.IGNORECASE
    #     )
    #
    #     if is_pattern:
    #         article = is_pattern.group(1)
    #         description = is_pattern.group(2).strip()
    #
    #         # 过滤掉太长或包含太多修饰词的描述
    #         if len(description.split()) <= 4 and not any(
    #                 word in description.lower() for word in ['who', 'which', 'that']):
    #             return f"{entity_name} is {article} {description}."
    #
    #     # 如果无法提取简短描述，返回空
    #     return ""

    def _extract_concise_description(self, abstract: str, entity_name: str, std_entity_type: str) -> str:
        """从摘要中提取最精简的描述"""
        if not abstract:
            return ""

        # 清理文本
        cleaned = self._basic_cleaning(abstract)
        first_sentence = self._extract_first_sentence(cleaned)

        print(f"DEBUG - First sentence for {entity_name}: {first_sentence[:150]}...")  # 添加调试

        if not first_sentence:
            return ""

        # 改进的正则表达式模式
        patterns = [
            # 原有模式，但增加长度限制
            r'(?:is|was)\s+(a|an)\s+([^,\.]{3,80})(?:[,\.]|$)',
            # 新增模式：处理"is the"结构
            r'(?:is|was)\s+(the)\s+([^,\.]{3,80})(?:[,\.]|$)',
            # 新增模式：处理直接描述
            r'(?:is|was)\s+([^,\.]{10,100})(?:[,\.]|$)',
        ]

        for i, pattern in enumerate(patterns):
            match = re.search(pattern, first_sentence, re.IGNORECASE)
            if match:
                print(f"DEBUG - Pattern {i + 1} matched for {entity_name}")

                if len(match.groups()) == 2:
                    article = match.group(1)
                    description = match.group(2).strip()
                else:
                    article = ""
                    description = match.group(1).strip()

                # 清理描述
                description = self._clean_description(description)
                print(f"DEBUG - Extracted description: '{description}', words: {len(description.split())}")

                # 更宽松的过滤条件
                if (len(description.split()) <= 12 and
                        len(description) <= 100 and
                        not any(word in description.lower() for word in ['who', 'which', 'that', 'where', 'when'])):

                    if article:
                        result = f"{entity_name} is {article} {description}."
                    else:
                        result = f"{entity_name} is {description}."

                    print(f"DEBUG - Final result: {result}")
                    return result

        print(f"DEBUG - No suitable pattern found for {entity_name}")
        return ""

    def _clean_description(self, description: str) -> str:
        """清理描述文本"""
        # 移除多余的修饰词
        description = re.sub(r'\b(?:very|quite|rather|extremely|highly)\b', '', description)

        # 移除括号内容
        description = re.sub(r'\([^)]*\)', '', description)

        # 移除多余空格
        description = re.sub(r'\s+', ' ', description).strip()

        # 如果以连词结束，移除连词
        description = re.sub(r'\s+(and|or|but)$', '', description)

        return description


    def _extract_core_description(self, description: str) -> str:
        """提取描述的核心部分"""
        # 移除常见的修饰词和短语
        description = re.sub(r'\b(?:major|large|small|important|famous|well-known)\b', '', description)
        description = re.sub(r'\s+', ' ', description).strip()

        # 如果还是太长，取前几个词
        words = description.split()
        if len(words) > 4:
            return ' '.join(words[:4])

        return description if len(words) > 0 else ""


    def _extract_last_part(self, uri: str) -> str:
        """从URI中提取最后部分并格式化"""
        if not uri:
            return ""
        return uri.split('/')[-1].replace('_', ' ').lower()

    def _basic_cleaning(self, text: str) -> str:
        """基础文本清理"""
        if not text:
            return ""

        # 移除HTML标签
        text = re.sub(r'<[^>]+>', '', text)
        # 移除引用标记
        text = re.sub(r'\[\d+\]', '', text)
        # 移除括号内的日期信息
        text = re.sub(r'\([^)]*\d{4}[^)]*\)', '', text)
        text = re.sub(r'\([^)]*born[^)]*\)', '', text, flags=re.IGNORECASE)
        # 标准化空格
        text = re.sub(r'\s+', ' ', text).strip()

        return text

    def _extract_first_sentence(self, text: str) -> str:
        """提取第一个句子"""
        if not text:
            return ""

        # 按句号分割，但保留缩写中的句号
        sentence_pattern = r'(?<!\w\.\w.)(?<![A-Z][a-z]\.)(?<=\.|\?|\!)\s'
        sentences = re.split(sentence_pattern, text)

        if sentences:
            return sentences[0].strip()
        return text

    def _get_fallback_description(self, entity_type: str, ner_model: str) -> str:
        """根据NER模型获取相应的备用描述"""
        fallback_mappings = {
            "conll3": {
                "PER": "a person",
                "ORG": "an organization",
                "LOC": "a location",
                "MISC": "an entity"
            },
            "ontonotes": {
                "PERSON": "a person",
                "ORG": "an organization",
                "GPE": "a place",
                "LOC": "a location",
                "FAC": "a facility",
                "EVENT": "an event",
                "WORK_OF_ART": "a work of art",
                "PRODUCT": "a product",
                "NORP": "a group",
                "LANGUAGE": "a language",
                "LAW": "a law",
                "DATE": "a date",
                "TIME": "a time",
                "PERCENT": "a percentage",
                "MONEY": "an amount of money",
                "QUANTITY": "a quantity",
                "ORDINAL": "an ordinal number",
                "CARDINAL": "a number"
            },
            "azure": {
                "Person": "a person",
                "PersonType": "a person type",
                "Organization": "an organization",
                "Location": "a location",
                "Event": "an event",
                "Product": "a product",
                "Skill": "a skill",
                "Address": "an address",
                "PhoneNumber": "a phone number",
                "Email": "an email address",
                "URL": "a web address",
                "IP": "an IP address",
                "DateTime": "a date and time",
                "Quantity": "a quantity"
            },
            "aws": {
                "PERSON": "a person",
                "ORGANIZATION": "an organization",
                "LOCATION": "a location",
                "COMMERCIAL_ITEM": "a product",
                "EVENT": "an event",
                "DATE": "a date",
                "QUANTITY": "a quantity",
                "TITLE": "a creative work",
                "OTHER": "an entity"
            }
        }

        model_fallbacks = fallback_mappings.get(ner_model.lower(), {})
        return model_fallbacks.get(entity_type, "an entity")


# 为不同NER模型提供便利函数
def get_entity_description_dbpedia_conll3(entity_text: str, entity_type: str, session=None) -> str:
    """CoNLL-2003 NER模型专用"""
    processor = DBpediaDescriptionProcessor(session)
    return processor.get_entity_description(entity_text, entity_type, "conll3")


def get_entity_description_dbpedia_ontonotes(entity_text: str, entity_type: str, session=None) -> str:
    """OntoNotes NER模型专用"""
    processor = DBpediaDescriptionProcessor(session)
    return processor.get_entity_description(entity_text, entity_type, "ontonotes")


def get_entity_description_dbpedia_azure(entity_text: str, entity_type: str, session=None) -> str:
    """Azure NER模型专用"""
    processor = DBpediaDescriptionProcessor(session)
    return processor.get_entity_description(entity_text, entity_type, "azure")


def get_entity_description_dbpedia_aws(entity_text: str, entity_type: str, session=None) -> str:
    """AWS NER模型专用"""
    processor = DBpediaDescriptionProcessor(session)
    return processor.get_entity_description(entity_text, entity_type, "aws")


# 通用函数
def get_entity_description_dbpedia(entity_text: str, entity_type: str, ner_model: str, session=None) -> str:
    """
    通用的DBpedia实体描述获取函数

    Args:
        entity_text: 实体文本
        entity_type: 实体类型
        ner_model: NER模型 ("conll3", "ontonotes", "azure", "aws")
        session: 可选的requests会话

    Returns:
        str: 实体描述
    """
    processor = DBpediaDescriptionProcessor(session)
    return processor.get_entity_description(entity_text, entity_type, ner_model)