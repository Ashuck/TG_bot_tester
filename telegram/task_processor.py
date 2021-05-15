from yaml import load
from dataclasses import dataclass, field
import re


@dataclass
class Task:
    command: str
    description: str
    task_type: str
    timeout: int
    messages: list


@dataclass
class Error:
    task: str
    sub_task: str
    alert: str


class TaskWorker:
    tasks = []
    errors = []

    def load_config_from_yaml(self, path):
        with open(path) as f:
            data = load(f)
        
        self.defaults = data['Defaults']
        self.raw_tasks = data["Tasks"]

        for t in self.raw_tasks:
            for_task = {**self.defaults, **t}
            self.tasks.append(Task(**for_task))
    

    def check_task(self, sub_task, messages):
        errors = []
        for num, msg in enumerate(messages, 1):
            alert = ''

            for regex in sub_task['regex']:
                if msg.text:
                    text = msg.text.markdown
                else:
                    text = msg.caption
                m = re.findall(regex, text)
                # print(text)
                if m:                   
                    alert = ''
                    break
                else:
                    alert += f'В тексте сообщения не найдено вхождение "{regex}"\n'

            if msg.reply_markup and msg.reply_markup.__dict__.get('inline_keyboard'):
                bot_kbr = msg.reply_markup['inline_keyboard']
                bot_btns = [btn for line in bot_kbr for btn in line]

                for btn in sub_task['inline_kbr']:
                    rigth_btn = None

                    for bot_btn in bot_btns:
                        if re.findall(btn['text'], bot_btn['text']):
                            rigth_btn = bot_btn
                            break

                    if rigth_btn:
                        if btn.get('url'):
                            alert += '' if re.findall(btn['url'], rigth_btn['url']) else f'Ссылка кнопки {btn["text"]} не совпадает с искомой\n'
                        elif btn.get('callback_data'):
                            
                            if re.findall(btn['callback_data'], rigth_btn['callback_data']):
                                for t in self.tasks:
                                    if t.task_type == 'call_back' and t.command == rigth_btn['callback_data']:
                                        t.id_msg = msg.message_id
                            else:
                                alert += f'callback_data кнопки {btn["text"]} не совпадает и искомой\n'
                    else:
                        alert += f'Не найдена кнопка {btn["text"]}\n'
                        

            elif sub_task['inline_kbr']:
                alert += 'В сообщении не найдена клавиатура\n'
            
            if not alert:
                sub_task['status'] = True
                break
            else:
                errors.append(
                    f'В сообщении №{num} найдены следующие ошибки:\n' + alert
                )

        if not sub_task.get('status'):
            
            return {'status': False, 'alert': ''.join(errors)}
        return {'status': True}
            
            
            
            
            
