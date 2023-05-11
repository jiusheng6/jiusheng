# coding=utf-8
import requests
import time

headers = {
 'content-length':'4212',
 'sec-ch-ua':'"Chromium";v="110", "Not A(Brand";v="24", "Google Chrome";v="110"',
 'accept':'application/json',
 'content-type':'application/json',
 'sec-ch-ua-mobile':'?0',
 'user-agent':'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.0.0 Safari/537.36',
 'sec-ch-ua-platform':'"Windows"',
 'origin':'https://openai.com',
 'sec-fetch-site':'cross-site',
 'sec-fetch-mode':'cors',
 'sec-fetch-dest':'empty',
 'accept-encoding':'gzip, deflate, br',
 'accept-language':'zh-CN,zh;q=0.9'}
sheng = ["org-Fo8AiNdYLlIm4jOaOdIWLbyr","org-98GjJP8Qi0nSmiUJLdRhuHKf","org-C7WOd15Srr1ZLoTB8KXTaDvK","org-5yPWgW6eo9ymlJyLAilMADsQ","org-nch2Gth5Mo84FWrzo7JwKtjk","org-tP8s5bm2md5irvxOmF0bzRiP","org-7p17aLQQsaQtJZEAHskQ1mD8","org-nch2Gth5Mo84FWrzo7JwKtjk"]



for i in sheng:
 jiu = '{"fields":[{"name":"firstname","value":"qin","objectTypeId":"0-1"},{"name":"lastname","value":"zhi","objectTypeId":"0-1"},{"name":"email","value":"qingzhijiusheng@gmail.com","objectTypeId":"0-1"},{"name":"company","value":"qinzhi","objectTypeId":"0-1"},{"name":"openai_api_organization_id","value":"' + i + '","objectTypeId":"0-1"},{"name":"codex_primary_use","value":"Build a new product / application","objectTypeId":"0-1"},{"name":"codex_ideas","value":"Dear OpenAI Team,\\n\\nI hope this email finds you well. I am writing to express my interest in obtaining access to the API for your latest model, GPT-4. As a passionate developer and AI enthusiast, I am eager to explore the capabilities of the GPT-4 and implement it in my projects.\\n\\nI have been following the progress of OpenAI\'s work closely and I am extremely impressed by the advancements made in the field of artificial intelligence, particularly with the GPT series. The release of GPT-3 has already paved the way for incredible innovations, and I believe GPT-4 will bring us even closer to achieving human-like language understanding.\\n\\nAs a developer, I am constantly seeking opportunities to create useful and engaging applications. I believe that having access to the GPT-4 API will allow me to create groundbreaking solutions in various areas, such as natural language processing, content generation, and sentiment analysis, among others. I am confident that the insights I gain from working with GPT-4 will greatly benefit both my personal growth and the projects I am involved in. Additionally, I am committed to using this technology responsibly and ethically, ensuring that it contributes positively to society.\\n\\nIn order to facilitate my application, I have provided some information about my background and my intended use of the GPT-4 API:\\n\\nName: qinzhi\\nEmail address: stepcounsothane@mail.com\\nUse Case Description: As a developer, I plan to utilize the GPT-4 API to build new products that cater to the needs of various industries and domains. Here are some specific use cases where I intend to apply the GPT-4 API:\\nAutomatic content generation: Leverage GPT-4\'s powerful natural language understanding and generation capabilities to create high-quality textual content for users, such as blog articles, social media posts, advertising copy, and more.\\n\\nIntelligent chatbots: Develop highly interactive and responsive chatbots that provide real-time assistance to users, such as customer support, shopping advice, and general inquiries.\\n\\nLanguage translation: Harness GPT-4\'s multilingual capabilities to provide real-time language translation, helping users overcome language barriers and achieve seamless communication.\\n\\nText summarization and analysis: Offer text summarization and key point extraction features to help users quickly grasp the main content of large amounts of material. Additionally, employ sentiment analysis to evaluate the emotional tone of the text, providing valuable feedback to users.\\n\\nAutomated question-answering systems: Create automated question-answering systems targeted at specific domains, such as healthcare, legal, education, and more, offering users expert and accurate information.\\n\\nI believe the GPT-4 API will be the driving force behind these products, providing unprecedented convenience and value to users. I will closely monitor user needs and feedback to continuously optimize the products, ensuring responsible and ethical use of GPT-4 technology and making a positive impact on society.\\nI would like to take this opportunity to thank you for considering my application. I understand that the demand for access to the GPT-4 API is high, and I appreciate the efforts that the OpenAI team has put in to build and maintain this sophisticated technology.\\n\\nPlease do not hesitate to contact me if you require any further information or clarification. I am looking forward to the possibility of working with GPT-4 and contributing to the development of AI technologies.\\n\\nThank you for your time and attention.\\n\\nBest regards,\\nqinzhi","objectTypeId":"0-1"}],"context":{"pageUri":"https://openai.com/waitlist/gpt-4-api","pageName":"GPT-4 API waitlist"}}'
 response0 = requests.request("POST",
                              "https://api.hsforms.com/submissions/v3/integration/submit/8050860/2d219882-f7f1-45ee-bba3-cbfc22f2a53d",
                              headers=headers, data=jiu)
 time.sleep(30)
 if response0.status_code >= 200 and response0.status_code < 300:
  print("请求成功! 组织ID：{}".format(i))
  print("等待30秒！")


 else:
  print("请求失败! 组织ID：{}".format(i))
  print("等待10秒！")





