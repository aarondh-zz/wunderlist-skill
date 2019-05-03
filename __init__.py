from mycroft import MycroftSkill, intent_file_handler
from mycroft.util.log import getLogger
import re
import wunderpy2
import phonetics

__author__ = "aarondh"

LOGGER = getLogger(__name__)

api = wunderpy2.WunderApi()


class Wunderlist(MycroftSkill):
    def __init__(self):
        MycroftSkill.__init__(self) 
        self.client = ''

    def get_access_count(self):
        if self.settings.get('access_count'):
            return self.settings.get('access_count')
        else:
            return 0
        
    def increment_access_count(self):
        self.settings['access_count'] = self.get_access_count() + 1
            
    def clear_access_count(self):
        self.settings['access_count'] = 0
        
    def get_client_secret(self):
        if not self.settings.get('client_secret'):
            self.speak_dialog('i.do.not.know',
                              data={'thing': 'client secret'})
        return self.settings.get('client_secret')

    def get_temporary_code(self):
        if not self.settings.get('temporary_code'):
            self.speak_dialog('i.do.not.know',
                              data={'thing': 'temporary code'})
        return self.settings.get('temporary_code')

    def get_access_token(self):
        if not self.settings.get('access_token'):
            if self.get_temporary_code():
                self.settings['access_token'] = api.get_access_token(self.get_temporary_code(),
                                                         self.get_client_id(),
                                                         self.get_client_secret())
        return self.settings.get('access_token')
        
    def normalize_name(self, name):
        to = re.sub('[^\w]+',' ', name.lower())
        #if self.is_debug():
        #    self.speak_dialog('normalized', data={'from':name,'to':to})
        return to
    
    def match_names(self, name_a, name_b):
        return self.phonetic_match(name_a, name_b)
    
    def phonetic_match(self, text_a, name_b):
        return phonetics.metaphone(text_a) == phonetics.metaphone(name_b)

    def get_client_id(self):
        if not self.settings.get('client_id'):
            self.speak_dialog('i.do.not.know', data={'thing': 'client id'})
        return self.settings.get('client_id')

    def get_client(self):
        if not self.client:
            if self.get_access_token():
                self.client = api.get_client(self.get_access_token(),
                                             self.get_client_id())
                                             
        if self.is_debug() or self.get_access_count() == 0:
            self.speak_dialog('access.to',data={'doordonot': ('do' if self.client else 'do not')})
            if self.client:
                self.increment_access_count()
        else:
            self.increment_access_count()
            
        return self.client
        
    def is_debug(self):
        return self.settings.get('debug')
        
    def get_default_listname(self):
        return self.settings.get('default_listname')

    def set_default_listname(self, listname):
        self.settings['default_listname'] = listname
        
    def find_list_by_name(self, listname):
        client = self.get_client()
        if client:
            lists = client.get_lists()
            for list in lists:
                if self.match_names(listname, self.normalize_name(list.get('title'))):
                    return list
        self.speak_dialog('list.not.found',data={'listname': listname})
        return None
        
    def read_list_by_name(self, listname):
        list = self.find_list_by_name(listname)
        if list:
            client = self.get_client()
            tasks = client.get_tasks(list.get('id'))
            number_of_tasks = len(tasks)
            if number_of_tasks > 3:
                self.speak_dialog('read.list', data={'listname': listname,'number_of_tasks': str(number_of_tasks)})
                for i, task in enumerate(tasks):
                    self.speak_dialog(str(i+1) + ", " +task.get('title'))
            elif number_of_tasks == 0:
                self.speak_dialog('you.have.no.tasks')
            elif number_of_tasks == 1:
                self.speak_dialog('one.task',data={'one': tasks[0].get('title')})
            elif number_of_tasks == 2:
                self.speak_dialog('two.tasks',data={'one': tasks[0].get('title'),'two': tasks[1].get('title')})
            elif number_of_tasks == 3:
                self.speak_dialog('three.tasks',data={'one': tasks[0].get('title'),'two': tasks[1].get('title'),'three': tasks[2].get('title')})
            
    @intent_file_handler('readmylist.intent')
    def handle_readmylist(self, message):
        if message.data.get("listname"):
            listname = str(message.data.get("listname"))
            self.read_list_by_name(listname)
        else:
            self.speak_dialog('which.list')

    @intent_file_handler('list.intent')
    def handle_list(self, message):
        client = self.get_client()
        if client:
            lists = client.get_lists()
            list_titles = []
            for i,list in enumerate(lists):
                list_titles.append(list.get('title'))

            self.speak_dialog('these.are.your.lists', data={'titles':', '.join(list_titles)})
            
    @intent_file_handler('debug.intent')
    def handle_debug(self, message):
        debug_state = str(message.data.get('debugstate'))
        self.settings['debug'] = debug_state == 'on'
        self.speak_dialog('debug.is', data={'state': ('on' if self.is_debug() else 'off')})
        
    @intent_file_handler('whatdefault.intent')
    def handle_whatdefault(self, message):
        if self.get_default_listname():
            self.speak_dialog('your.default.list',data={'listname':self.get_default_listname()})
        else:
            self.speak_dialog('you.have.no.default.list')
            
    @intent_file_handler('letslook.intent')
    def handle_letslook(self, message):
        listname = message.data.get('listname')
        list = self.find_list_by_name(listname)
        if list:
            listname = list.get('title')
            self.set_context('listname',listname);
            self.speak_dialog('oklets',data={'listname':listname}, expect_response=True)
        
    @intent_file_handler('setdefaultlist.intent')
    def handle_setdefaultlist(self, message):
        listname = message.data.get('listname')
        list = self.find_list_by_name(listname)
        if list:
            listname = list.get('title')
            self.set_default_listname(listname);
            self.speak_dialog('your.default.list',data={'listname':self.get_default_listname()}, expect_response=True)          
        
    @intent_file_handler('whattasks.intent')
    def handle_whattasks(self, message):
        listname = message.data.get('listname')
        if not listname:
            listname = self.get_default_listname()
        if listname:
            self.read_list_by_name(listname)
        else:
            self.speak_dialog('you.have.no.default.list')
            
    @intent_file_handler('love.intent')
    def handle_love(self, message):
        self.speak_dialog('aaron.loves.donna')


def create_skill():
    return Wunderlist()
