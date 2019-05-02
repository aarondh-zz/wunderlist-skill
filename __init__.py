from mycroft import MycroftSkill, intent_file_handler


class Wunderlist(MycroftSkill):
    def __init__(self):
        MycroftSkill.__init__(self)

    @intent_file_handler('wunderlist.intent')
    def handle_wunderlist(self, message):
        self.speak_dialog('wunderlist')


def create_skill():
    return Wunderlist()

