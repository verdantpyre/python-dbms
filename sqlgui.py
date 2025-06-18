import sqlite3
import tkinter as tk
import tkinter.font as tkFont
from tkinter import ttk
from tkinter import filedialog as fd
import csv
import pickle
import os
from tkinter.font import families
# pip install pandas must be used
# pip install odfpy
# pip install openpyxl
import pandas as pd
import numpy
import sqlite3 as sql


class NotUnique(Exception):
    pass

class EmptyEntry(Exception):
    pass

class WrongDataType(Exception):
    pass

class UndefType(Exception):
    pass

class ForeignKeyInteg(Exception):
    pass


class MainScreen:
    def __init__(self):
        global theme, fontpack
        # Regenerate any missing file or directories to their default version
        if not os.path.isdir('AppData'):
            os.mkdir('AppData')
        if not os.path.isdir('AppData/Presets'):
            os.mkdir('AppData/Presets')
            with open('AppData/Presets/Attendance.csv', 'w') as f:
                csv.writer(f).writerows([['roll', 'name', 'class', 'present', 'total'],
                                         ['primary key','none', 'none', 'none', 'none'],
                                         ['integer', 'varchar', 'varchar', 'integer', 'integer'],
                                         ['','','','', '']])
            with open('AppData/Presets/Marks.csv', 'w') as f:
                csv.writer(f).writerows([['roll', 'name', 'class', 'day', 'percentage'],
                                         ['primary key', 'none', 'none', 'none', 'none'],
                                         ['integer', 'varchar', 'varchar', 'date', 'number'],
                                         ['', '', '', '', '']])
        if not os.path.isfile('AppData/pass.dat'):
            opensetmast()
        try:
            with open('AppData/pref.dat', 'rb') as f:
                r = pickle.load(f)
        except:
            with open('AppData/pref.dat', 'wb') as f:
                r = (['Calibri', 18], 'Dark')
                pickle.dump(r, f)
        self.user = None
        self.master = False
        self.presets = []
        self.defaultp = []
        self.subitemuser = None
        self.themename = r[1]
        theme = themes[self.themename]
        fontpack = r[0]
        self.current = "None"
        self.subitem = None

        self.root = tk.Tk()
        self.updatefont()
        self.root.title('Application')
        self.root.geometry('700x500')
        self.root.protocol("WM_DELETE_WINDOW", lambda: self.onexit(1))

        self.lprompt = Prompt(self.PassScreenOpen, 0)
        self.lprompt.screen.title("Enter Details")
        self.lprompt.new = tk.Label(self.lprompt.screen, text='Username not found.')
        self.lprompt.newbutton = tk.Button(self.lprompt.screen, text='Create new user?', command=self.adduserdata)
        self.lprompt.wrong = tk.Label(self.lprompt.screen, text='Incorrect password.')

        self.wrongfiletypeprompt = Prompt(self.showwrongfiletype)
        self.wrongfiletypeprompt.screen.title('Wrong File Type')
        self.wrongfiletypeprompt.button = tk.Button(self.wrongfiletypeprompt.screen, text="Ok", command=self.wrongfiletypeprompt.close)
        self.wrongfiletypeprompt.label = tk.Label(self.wrongfiletypeprompt.screen, text='')

        self.wuserprompt = Prompt()
        self.wuserprompt.screen.title("Incorrect User Logged in")
        self.wuserprompt.label = tk.Label(self.wuserprompt.screen, text="Sorry! Cannot access this file.")
        self.wuserprompt.buttonframe = tk.Frame(self.wuserprompt.screen)
        self.wuserprompt.ok = tk.Button(self.wuserprompt.buttonframe, text="Ok", command=self.wuserprompt.close)
        self.wuserprompt.login = tk.Button(self.wuserprompt.buttonframe, text="Login", command=self.lprompt.open)
        self.wuserprompt.ok.grid(row=0, column=0)
        self.wuserprompt.login.grid(row=0, column=1)
        self.wuserprompt.action = lambda: self.promptload([self.wuserprompt.label, self.wuserprompt.buttonframe], [10, 0], [0, 10])

        self.crucial = Prompt()
        self.crucial.screen.title("File off limits")
        self.crucial.label = tk.Label(self.crucial.screen, text="Sorry! Cannot access this file.")
        self.crucial.action = lambda: self.promptload([self.crucial.label], [10], [0], self.crucial)

        self.cpresql = Prompt()
        self.cpresql.screen.title("Can't Open Preset")
        self.cpresql.label = tk.Label(self.cpresql.screen, text="Sorry! You cannot edit\npresets with SQL.")
        self.cpresql.action = lambda: self.promptload([self.cpresql.label], [10], [0], self.cpresql)

        self.loaderror = Prompt()
        self.loaderror.screen.title("Loading Error Occured")
        self.loaderror.label = tk.Label(self.loaderror.screen, text="Sorry! An error occured while loading\nthis file. Default data was inserted.")
        self.loaderror.action = lambda: self.promptload([self.loaderror.label], [10], [0], self.loaderror)

        self.fontprompt = Prompt(self.customfont, 0)
        self.fontprompt.cur = fontpack[0]
        self.fontprompt.screen.title("Enter Font Name")
        self.fontprompt.ent = tk.Entry(self.fontprompt.screen)
        self.fontprompt.button = tk.Button(self.fontprompt.screen, text="Go", command=lambda: self.changefont(custom=True))

        self.wdatatype = Prompt(self.showwrongdatatype)
        self.wdatatype.screen.title("Integrity Error Occured")
        self.wdatatype.button = tk.Button(self.wdatatype.screen, text="Ok", command=self.wdatatype.close)
        self.wdatatype.label = tk.Label(self.wdatatype.screen, text='')

        self.emptydefault = Prompt()
        self.emptydefault.screen.title('Empty Default Value Entered')
        self.emptydefault.label = tk.Label(self.emptydefault.screen, text="Default constraint can't\nhave empty value\nenter a value")
        self.emptydefault.action = lambda: self.promptload([self.emptydefault.label], [10], [0], self.emptydefault)

        self.multipri = Prompt()
        self.multipri.screen.title('Empty Default Value Entered')
        self.multipri.label = tk.Label(self.multipri.screen, text="Table cannot have more\nthan one primary key")
        self.multipri.action = lambda: self.promptload([self.multipri.label], [10], [0], self.multipri)


        self.errormessages = [self.lprompt.new, self.lprompt.wrong, self.crucial.label, self.wrongfiletypeprompt.label,
                              self.wdatatype.label, self.wuserprompt.label, self.emptydefault.label, self.loaderror.label,
                              self.multipri.label, self.cpresql.label]

        self.subprompts = []

        self.addmenubar()
        self.changetheme(self.themename)
        self.root.mainloop()

    def Open(self, type='Table', isnew=True, preset=None):
        for w in Prompt.active:
            w.close()
        if not self.onopen():
            return
        asked = False
        if type == 'SQL':
            fn = fd.asksaveasfilename(confirmoverwrite=False, filetypes=filetypes[1:2])
            if len(fn) == 0:
                return
            fn = fn.strip()
            acc = self.canaccess(fn)
            if acc == 'xuser':
                self.wuserprompt.open()
            elif acc == 'never':
                self.crucial.open()
            elif acc == 'can edit':
                tz = fn.split('.')[0]
                if tz != 'db':
                    self.wrongfiletypeprompt.open(f'Cannot open .{tz}\ntry Database types.')
                else:
                    self.finalizeopen('SQL', fn)
            else:
                self.cpresql.open()
            return
        if isnew or type=='any':
            if type == 'Table':
                self.finalizeopen('Table', None, preset)
                return
            elif type == 'Database':
                self.finalizeopen('Database',None, preset)
                return
            asked = True
            fn = preset
        if not asked:
            fn = fd.askopenfilename(filetypes=filetypes)
            if len(fn) == 0:
                return
            fn = fn.strip()
        ft = fn.split('.')[-1].lower()
        acc = self.canaccess(fn)
        pset = None
        rset = fn
        if acc == 'xuser':
            self.wuserprompt.open()
            return
        elif acc == 'never':
            self.crucial.open()
            return
        elif acc == 'only load':
            pset, rset = rset, pset
        if ft == 'db':
            self.finalizeopen('Database', rset, pset)
        elif ft in excelt:
            d = pd.ExcelFile(fn)
            d.sheet_names
            if len(d.sheet_names) == 1:
                self.finalizeopen('Table', rset, pset)
            else:
                self.finalizeopen('Database', rset, pset)
            d.close()
        else:
            self.finalizeopen('Table', rset, pset)

    def promptload(self, widgets=[], padx=[], pady=[], ok=0):
        for i in range(len(widgets)):
            widgets[i].pack(padx=padx[i], pady=pady[i])
        if ok != 0:
            tk.Button(ok.screen, text='Ok', command=ok.close, bg=theme[3], fg=theme[4]).pack(pady=10)

    def showwrongfiletype(self, label):
        self.wrongfiletypeprompt.label.config(text=label[0])
        self.promptload([self.wrongfiletypeprompt.label, self.wrongfiletypeprompt.button], [10, 0], [0, 10])

    def showwrongdatatype(self, label):
        self.wdatatype.label.config(text=label[0])
        self.promptload([self.wdatatype.label, self.wdatatype.button], [10, 0], [0, 10])

    def finalizeopen(self, type, path=None, preset=None):
        global conslist
        if self.current != 'None':
            self.subitem.mainframe.destroy()
        self.menubar.entryconfigure(5, label='Back')
        self.current = type
        self.filemenu.entryconfigure('Save As', state=tk.NORMAL)
        if type == 'Table':
            conslist = ['primary key', 'unique', 'default', 'not null', 'none']
            self.subitem = Table(self, self.root, False, path, preset)
        elif type == 'Database':
            conslist = ['primary key', 'foreign key', 'unique', 'default', 'not null', 'none']
            self.subitem = Database(self, path, preset)
        elif type == 'SQL':
            self.filemenu.entryconfigure('Save As', state=tk.DISABLED)
            self.subitem = SQL(self.root, path, self.user)
        if preset != None:
            self.subitem.path = None

        self.subitem.user = self.user
        s = f'/User {self.user}/'
        if s in str(path) or s in str(preset):
            self.subitemuser = None
        else:
            self.subitemuser = self.user
        self.subitem.tk_display()

    def canaccess(self, path):
        p = path.split('/')
        if p[-3] == "AppData":
            if p[-2] == f"User {self.user}":
                return 'can edit'
            elif p[-2] == 'Presets':
                return 'only load'
            else:
                if self.master:
                    return 'can edit'
                return 'xuser'
        elif p[-4] == 'AppData':
            if p[-3:-1] == [f'User {self.user}', 'Presets']:
                return 'only load'
            else:
                if self.master:
                    return 'only load'
                return 'xuser'
        elif p[-2:] == ["AppData", 'pass.dat'] or p[-2:] == ["AppData", 'pref.dat']:
            return 'never'
        else:
            return 'can edit'

    def PassScreenOpen(self):
        self.lprompt.wrongexists = False
        self.lprompt.newexists = False
        if self.wuserprompt in Prompt.active:
            self.wuserprompt.close()
        tk.Label(self.lprompt.screen, text='Username:', bg=theme[2], fg=theme[0]).pack()
        self.lprompt.usent = tk.Entry(self.lprompt.screen, bg=theme[1], fg=theme[0])
        self.lprompt.usent.pack(padx=20)
        tk.Label(self.lprompt.screen, text='Password:', bg=theme[2], fg=theme[0]).pack()
        self.lprompt.psent = tk.Entry(self.lprompt.screen, bg=theme[1], fg=theme[0])
        self.lprompt.psent.pack(padx=20)
        tk.Button(self.lprompt.screen, text='Enter', command=self.LoginUserLogic, bg = theme[3], fg=theme[4]).pack(pady=10)

    def LoginUserLogic(self):
        user = self.lprompt.usent.get().strip()
        pas = self.lprompt.psent.get().strip()
        if len(user) == 0 or len(pas) == 0:
            return
        f = open('AppData/pass.dat', 'rb')
        pmat = []
        usrlst = []
        try:
            while True:
                obj = pickle.load(f)
                pmat.append(obj)
                usrlst.append(obj[0])
        except EOFError:
            pass

        if not any(usr == user for usr in usrlst):
            if not self.lprompt.newexists:
                self.lprompt.newexists = True
                if self.lprompt.wrongexists:
                    self.lprompt.wrong.pack_forget()
                    self.lprompt.wrongexists = False
                self.lprompt.new.pack()
                self.lprompt.newbutton.pack(pady=10)
            return
        else:
            corpas = pmat[usrlst.index(user)][1]
        if pas == corpas:
            self.lprompt.close()
            if user == usrlst[0]:
                self.master = True
            self.user = user
            if self.current != 'None':
                self.subitem.user = user
            self.menubar.entryconfigure(2, label='Logout', command=self.LogoutLogic)
            self.loadpresets()
        elif pas != corpas:
            if self.lprompt.newexists:
                self.lprompt.new.pack_forget()
                self.lprompt.newbutton.pack_forget()
                self.lprompt.newexists = False
            if not self.lprompt.wrongexists:
                self.lprompt.wrongexists = True
                self.lprompt.wrong.pack(pady=10)
                self.errormessages.append(self.lprompt.wrong)
                self.errormessages.append(self.lprompt.wrong)
                self.lprompt.screen.mainloop()

    def adduserdata(self):
        user = self.lprompt.usent.get()
        pas = self.lprompt.psent.get()
        if user == 'None':
            return
        f = open('AppData/pass.dat', 'ab')
        pickle.dump([user, pas, fontpack], f)
        f.close()
        os.mkdir(f'AppData/User {user}' )
        os.mkdir(f'AppData/User {user}/Presets' )
        self.lprompt.close()
        self.user = user
        if self.current != 'None':
            self.subitem.user = user
        self.menubar.entryconfigure(2, label='Logout', command=self.LogoutLogic)
        self.loadpresets()

    def LogoutLogic(self):
        if self.subitemuser != None:
            if self.onexit(leave=False):
                self.user = None
                self.subitemuser = None
                self.master = False
                self.menubar.entryconfigure(2, label="Login", command=self.lprompt.open)
                self.loadpresets()
        else:
            self.user = None
            self.master = False
            self.menubar.entryconfigure(2, label="Login", command=self.lprompt.open)
            self.loadpresets()

    def changetheme(self, name='Dark'):
        global theme
        self.preferencemenu.entryconfigure(2, label=f'Theme: {name}')
        self.themename = name
        theme = themes[name]
        self.menubar.config(bg = theme[3], fg=theme[4])
        self.preferencemenu.config(bg=theme[3], fg=theme[4])
        self.filemenu.config(bg=theme[3], fg=theme[4])
        self.fontoption.config(bg=theme[3], fg=theme[4])
        self.fontsizeoption.config(bg=theme[3], fg=theme[4])
        self.thememenu.config(bg=theme[3], fg=theme[4])
        self.saveasmenu.config(bg=theme[3], fg=theme[4])
        self.newoptions.config(bg=theme[3], fg=theme[4])
        self.custompresets.config(bg=theme[3], fg=theme[4])
        self.update_children(self.root)

    def updatefont(self):
        tkFont.nametofont("TkDefaultFont").configure(family=fontpack[0], size=fontpack[1])
        tkFont.nametofont("TkTextFont").configure(family=fontpack[0], size=fontpack[1])
        tkFont.nametofont("TkMenuFont").configure(family=fontpack[0], size=fontpack[1])
        tkFont.nametofont("TkHeadingFont").configure(family=fontpack[0], size=fontpack[1])

    def update_children(self, window):
        window.config(bg=theme[2])
        for w in window.winfo_children():
            if isinstance(w, tk.Entry) or isinstance(w, tk.OptionMenu):
                w.config(fg=theme[0], bg=theme[1])
            elif isinstance(w, tk.Button):
                w.config(fg=theme[4], bg=theme[3])# 01728725
            elif isinstance(w, tk.Text):
                w.config(fg=theme[4], bg=theme[3])
            elif isinstance(w, tk.Label):
                if w in self.errormessages:
                    w.config(fg=theme[5], bg=theme[2])
                else:
                    w.config(bg=theme[2], fg=theme[0])
            elif isinstance(w, tk.Frame) or isinstance(w, tk.Canvas) or isinstance(w, tk.Toplevel):
                self.update_children(w)

    def changefont(self, font=False, size=False, custom=False):
        if font:
            fontpack[0] = font
            self.preferencemenu.entryconfigure(0, label=f'Font: {font}')
        if size:
            fontpack[1] = size
            self.preferencemenu.entryconfigure(1, label=f'Font: {size}')
        if custom:
            font = self.fontprompt.ent.get().strip()
            self.fontprompt.cur = font
            fontpack[0] = font
            self.fontoption.entryconfigure(19, label=f"Custom: {font}")
            self.preferencemenu.entryconfigure(0, label=f'Font: {font}')
        self.updatefont()
        self.fontprompt.close()

    def customfont(self):
        self.fontprompt.ent.delete(0, tk.END)
        self.fontprompt.ent.insert(0, self.fontprompt.cur)
        self.fontprompt.ent.pack(padx=10)
        self.fontprompt.button.pack(pady=5)

    def addmenubar(self):
        self.menubar = tk.Menu(self.root)
        self.filemenu = tk.Menu(self.menubar, tearoff=0)
        self.filemenu.add_command(label='Open', command=lambda: self.Open(isnew = False))

        self.newoptions = tk.Menu(self.filemenu, tearoff=0)
        self.newoptions.add_command(label='Empty Table', command=lambda: self.Open('Table'))
        self.newoptions.add_command(label='Empty Database', command=lambda: self.Open('Database'))
        self.custompresets = tk.Menu(self.newoptions, tearoff=0)
        self.newoptions.add_cascade(menu=self.custompresets, label='Custom Presets')
        self.loadpresets()
        self.filemenu.add_cascade(menu=self.newoptions, label='New')

        self.filemenu.add_command(label='Save', command=lambda: self.savecurrent())
        self.saveasmenu = tk.Menu(self.filemenu, tearoff=0)
        self.saveasmenu.add_command(label='File', command=lambda: self.savecurrent('newfile'))
        self.saveasmenu.add_command(label='Preset', command=lambda: self.savecurrent('preset'))
        self.filemenu.add_cascade(menu=self.saveasmenu, label='Save As')
        self.menubar.add_cascade(menu=self.filemenu, label="File")

        self.menubar.add_command(label='Login', command=self.lprompt.open)
        self.menubar.add_command(label="SQL", command=lambda: self.Open('SQL'))

        self.preferencemenu = tk.Menu(self.menubar, tearoff=0)

        self.fontoption = tk.Menu(self.preferencemenu, tearoff=0)
        self.thememenu = tk.Menu(self.preferencemenu, tearoff=0)
        self.fonts = ['Calibri', 'Helvetica', 'Laksaman', 'Latin Modern Math', 'Latin Modern Mono',
                      'Latin Modern Mono Prop', 'Latin Modern Mono Slanted', 'Latin Modern Roman', 'Latin Modern Roman',
                      'MathJax_Caligraphic', 'MathJax_Main', 'MathJax_Math', 'Nimbus Roman', 'Purisa',
                      'Standard Symbols PS', 'TeX Gyre Pagella', 'Times New Roman', 'URW Gothic', 'URW Palladio L']

        for f in self.fonts:
            self.fontoption.add_command(label=f, command=lambda f=f: self.changefont(f), font=(f, fontpack[1]))
        self.fontoption.add_command(label=f'Custom: {fontpack[0]}', command=self.fontprompt.open, font=fontpack)
        self.fontsizeoption = tk.Menu(self.preferencemenu, tearoff=0)
        for i in range(10, 45, 2):
            self.fontsizeoption.add_command(label=f'{i}', command=lambda i=i: self.changefont(size=i))
        for t in list(themes.keys()):
            self.thememenu.add_command(label=t, command=lambda t=t: self.changetheme(t))
        self.preferencemenu.add_cascade(menu=self.fontoption, label=f'Font: {fontpack[0]}')
        self.preferencemenu.add_cascade(menu=self.fontsizeoption, label=f'Size: {fontpack[1]}')
        self.preferencemenu.add_cascade(menu=self.thememenu, label=f'Theme: {self.themename}')
        self.menubar.add_cascade(menu=self.preferencemenu, label="Preferences")

        self.menubar.add_command(label="Exit", command=self.onexit)
        self.root.config(menu=self.menubar)

    def savecurrent(self, mode='normal'):
        if self.current == 'None':
            return
        if self.current == 'Table':
            try:
                newdat = self.subitem.out_matrix()
                n = hor_to_vert(newdat)
                for c in n:
                    checkcol(c)
            except NotUnique:
                self.wdatatype.open(f"Repeated entries present in\nfield '{c[0]}'")
                return
            except EmptyEntry:
                self.wdatatype.open(f"Empty entry present in\nfield '{c[0]}'")
                return
            except WrongDataType:
                self.wdatatype.open(f"Incorrect data type entry\npresent in field '{c[0]}'")
                return
            except UndefType:
                self.wdatatype.open(f"Data type not definded\nfor field '{c[0]}'")
                return
        elif self.current == 'Database':
            try:
                newdat = self.subitem.out_matrix()
                for t in list(newdat.keys()):
                    n = hor_to_vert(newdat[t])
                    for c in n:
                        try:
                            checkcol(c)
                        except ForeignKeyInteg:
                            f = self.subitem.tables[t].fields[newdat[t][0].index(c[0])]
                            mtmat = newdat[f.mtable]
                            rfi = mtmat[0].index(f.rfield)
                            cex = [mtmat[i][rfi] for i in range(len(mtmat))][3:]
                            if not all(en in cex for en in c[3:]):
                                self.wdatatype.open(
                                    f"Field '{c[0]}' of table '{t}'\n must have values present in field\n'{f.rfield}' of table '{f.mtable}'")
                                return
            except NotUnique:
                self.wdatatype.open(f"Repeated entries present in\nfield '{c[0]}' of table '{t}'")
                return
            except EmptyEntry:
                self.wdatatype.open(f"Empty entry present in\nfield '{c[0]}' of table '{t}'")
                return
            except WrongDataType:
                self.wdatatype.open(f"Incorrect data type entry present in\nfield '{c[0]}' of table '{t}'")
                return
            except UndefType:
                self.wdatatype.open(f"Data type not definded\nfor field '{c[0]}' of table '{t}'")
                return
        asked = False

        if mode == 'normal':
            for i in range(1):
                if self.subitem.path == None:
                    mode = 'newfile'
                    break
                self.subitem.saveself()
                return

        if mode == 'newfile':
            for i in range(1):
                if self.current == 'Table':
                    fn = fd.asksaveasfilename(filetypes=[('Table', tablef), ('Excel', excelf)])
                else:
                    fn = fd.asksaveasfilename(filetypes=[('Database', '.db'), ('Excel', excelf)])
                if len(fn) == 0:
                    return
                asked = True
                fn = fn.strip()
                acc = self.canaccess(fn)
                if acc == 'can edit':
                    self.subitem.savenew(fn)
                elif acc == 'only load':
                    mode = 'preset'
                    asked = True
                    break
                elif acc == 'xuser':
                    self.wuserprompt.open()
                    return
                elif acc == 'never':
                    self.crucial.open()
                    return

        if mode == 'preset':
            if not asked:
                if self.current == 'Table':
                    fn = fd.asksaveasfilename(filetypes=[('Table', tablef), ('Excel', excelf)])
                else:
                    fn = fd.asksaveasfilename(filetypes=[('Database', '.db'), ('Excel', excelf)])
                if len(fn) == 0:
                    return
            acc = self.canaccess(fn)
            if acc == 'only load':
                self.subitem.savenew(fn)
                self.loadpresets()
            elif acc == 'can edit':
                self.wdatatype.screen.title("Can't create presets here")
                self.wdatatype.open("Please choose a existing\npreset folder to\nsave a preset")
                self.wdatatype.screen.title("Wrong File Type")
                return
            elif acc == 'xuser':
                self.wuserprompt.open()
            elif acc == 'never':
                self.crucial.open()

    def getengine(self, ext):
        ext = ext.lower()
        if ext == 'ods':
            return 'odf'
        return 'openpyxl'

    def loadpresets(self):
        for i in self.presets:
            self.custompresets.delete(i)
        self.presets = []
        if self.user == None:
            pass
        else:
            self.presets = os.listdir(f'AppData/User {self.user}/Presets' )
            for i in self.presets:
                self.custompresets.add_command(label=i, command=lambda p=f'AppData/User {self.user}/Presets/{i}': self.Open('any', preset=p))
        for i in self.defaultp:
            self.newoptions.delete(i)
        self.defaultp = os.listdir('AppData/Presets')
        for i in self.defaultp:
            name = i
            type = i.split('.')[1]
            self.newoptions.add_command(label=i, command=lambda p=f'AppData/Presets/{i}': self.Open('any', preset=p))

    def onexit(self, main=0, leave=True):
        if self.current == 'None' and leave:
            with open('AppData/pref.dat', 'wb') as f:
                r = (fontpack, self.themename)
                pickle.dump(r, f)
            quit()
        if self.current in 'Table Database':
            dat = self.subitem.out_matrix()
            if dat != self.subitem.saveddata:
                a = MessageBox(self.root, "Unsaved Data", 'You have unsaved\nprogress on this\nfile.', [('Save', 1), ('Quit', -1), ('Cancel', 0)]).ask()
                if a == 1:
                    self.savecurrent()
                elif a == 0:
                    return 0
        elif self.current == 'SQL':
            if self.subitem.changed:
                a = MessageBox(self.root, "Unsaved Data", 'You have unsaved\nprogress on this\nfile.', [('Save', 1), ('Proceed', -1), ('Cancel', 0)]).ask()
                if a == 1:
                    self.savecurrent()
                elif a==0:
                    return 0
        if main:
            with open('AppData/pref.dat', 'wb') as f:
                r = (fontpack, self.themename)
                pickle.dump(r, f)
            quit()
        for w in self.root.winfo_children():
            if not isinstance(w, tk.Menu) and not isinstance(w, tk.Toplevel):
                w.destroy()
        for w in Prompt.active:
            w.close()
        self.menubar.entryconfigure(5, label='Exit')
        self.root.title('Application')
        self.subitem = None
        self.current = "None"
        self.filemenu.entryconfigure('Save As',state=tk.NORMAL)
        return 1

    def onopen(self):
        if self.current in 'Table Database':
            dat = self.subitem.out_matrix()
            if dat != self.subitem.saveddata:
                a = MessageBox(self.root,"Unsaved Data", 'You have unsaved\nprogress on this\nfile.', [('Save', 1), ('Proceed', -1), ('Cancel', 0)]).ask()
                if a == 1:
                    self.savecurrent()
                    return 1
                elif a == -1:
                    return 1
                else:
                    return 0
            else:
                return 1
        elif self.current == 'SQL':
            if not self.subitem.changed:
                return 1
            else:
                a = MessageBox(self.root, "Unsaved Data", 'You have unsaved\nprogress on this\nfile.', [('Save', 1), ('Proceed', -1), ('Cancel', 0)]).ask()
                if a == 1:
                    self.savecurrent()
                    return 1
                elif a == -1:
                    return 1
                else:
                    return 0
        elif self.current == 'None':
            return 1


class Database:
    def __init__(self, m, path=None, preset=None):
        self.mast = m
        self.path = path
        name = path
        self.preset = preset
        self.saveddata = {}
        self.curdata = {}
        self.user = m.user
        self.tables = {}
        self.tablebuttons = {}
        self.active = None
        self.tablecount = 0
        self.boxes = {}

        self.changetable = Prompt(self.changetablelogic, 0, self.swect)
        self.changetable.screen.title("Table Data")

        self.root = m.root
        self.mainframe = tk.Frame(self.root, bg=theme[2])
        self.buttonframe = tk.Frame(self.mainframe, bg=theme[2])
        self.buttonframe.grid(row=0, column=0, sticky='news')
        self.tableframe = tk.Frame(self.mainframe, bg=theme[2])
        self.tableframe.grid(row=0, column=1, sticky='news')
        if path != None:
            self.root.title(name)
            self.type = path.split('.')[-1].lower()
        else:
            self.root.title('Application')
            self.type = None
        self.load()

    def tk_display(self):
        self.mainframe.pack(fill=tk.BOTH, expand=1)
        self.buttoncanvas = tk.Canvas(self.buttonframe, bg=theme[2])
        self.buttoncanvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=1)
        self.buttonscrollbar = ttk.Scrollbar(self.buttonframe, orient=tk.VERTICAL, command=self.buttoncanvas.yview)
        self.buttonscrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.make_buttons()

    def load(self):
        if self.path == None:
            if self.preset==None:
                mat = [['field1'], ['none'], ['varchar'], ['']]
                self.tables['table1'] = Table(self.mast, self.tableframe, 1, None, mat, 'table1', self)
                self.curdata['table1'] = mat
                self.saveddata['table1'] = mat
                return
            else:
                self.path = self.preset
        self.path = self.path.strip()
        if self.type == 'db':
            self.db = sql.connect(self.path)
            self.cursor = self.db.cursor()
            lst = list(self.cursor.execute('select * from sqlite_schema;').fetchall())
            names = []
            for item in lst:
                if item[0] == 'table':
                    cons = []
                    typ = []
                    name = []
                    scheme = item[-1].partition('(')[-1].removesuffix(')').split(',')
                    for f in scheme:
                        t = f.split()
                        if len(t) == 1:
                            t += ['varchar']
                        if len(t) == 2:
                            t += ['none']
                        name.append(t[0].lower())
                        typ.append(t[1].lower())
                        cons.append(' '.join(t[2:]).lower())

                    mat = [name, cons, typ]
                    ret = self.cursor.execute(f'select * from {item[1]};').fetchall()
                    tabname = self.updatevalidname(item[1], names)
                    names.append(tabname)
                    for rec in ret:
                        mat.append(rec)
                    self.tables[tabname] = Table(self.mast, self.tableframe, 1, None, mat, tabname, self)
                    self.curdata[tabname] = self.tables[tabname].saveddata
                    self.saveddata[tabname] = self.tables[tabname].saveddata
                    if tabname != item[1]:
                        self.tables[tabname].olerror = True
            self.db.close()
        else:
            exfile = pd.ExcelFile(self.path)
            tables = exfile.sheet_names
            for tname in tables:
                raw = pd.DataFrame(pd.read_excel(exfile, sheet_name=tname))
                raw.replace(numpy.nan,'', inplace=True)
                mat = [list(raw.keys())]
                for r in raw.values:
                    mat.append([str(k).strip() for k in list(r)])
                self.tables[tname] = Table(self.mast, self.tableframe, 1, None, mat, tname, self)
                self.curdata[tname] = mat
                self.saveddata[tname] = mat
            exfile.close()

    def updatevalidname(self, name, set=[]):
        skipn = False
        tr = name
        for i in range(1):
            if not len(name):
                break
            n = name.split()
            if n[0] == 'default':
                break
            if len(n) > 1:
                tr = n[0]
                break
            if not checkname(name, set):
                break
            skipn = True
        if skipn:
            pass
        else:
            while True:
                if tr not in set:
                    break
                i += 1
                tr = f'table{i}'
            self.olerror = True
        return tr

    def make_buttons(self):
        self.buttoncanvas.configure(yscrollcommand=self.buttonscrollbar.set)
        self.buttoncanvas.bind('<Configure>', lambda e: self.buttoncanvas.configure(scrollregion=self.buttoncanvas.bbox("all")))

        self.subbuttonframe = tk.Frame(self.buttoncanvas, bg=theme[2])
        self.loadtablebutton = tk.Button(self.subbuttonframe, text="Load Table", command=self.asknewtable, bg=theme[3], fg=theme[4])
        self.emptytablebutton = tk.Button(self.subbuttonframe, text="Empty Table", command=lambda: self.asknewtable(0), bg=theme[3], fg=theme[4])
        self.loadtablebutton.grid(row=0, column=0, sticky='news')
        self.emptytablebutton.grid(row=1, column=0, sticky='news')
        tk.Label(self.subbuttonframe, bg=theme[3]).grid(row=2, column=0, sticky='news')
        for name in list(self.tables.keys()):
            self.tablebuttons[name] = tk.Button(self.subbuttonframe, text=name, bg=theme[3], fg=theme[4])
            self.tablebuttons[name].config(command=lambda n=name: self.changetable.open(n))
            self.tablebuttons[name].grid(row=self.tablecount + 3, column=0, sticky='news')
            self.tablecount += 1
        self.subbuttonframe.pack()

    def asknewtable(self, ask=True):
        if ask:
            fn = fd.askopenfilename(filetypes=filetypes)
            if len(fn) == 0:
                return
            fn = fn.strip()
            acc = self.mast.canaccess(fn)
        if not ask or acc in 'only load can edit':
            i = 1
            while True:
                s = f'table{i}'
                if s not in list(self.tables.keys()):
                    break
                i += 1
            if ask:
                self.tables[s] = Table(self.mast, self.tableframe, 2, fn, None, s, self)
                self.curdata[s] = self.tables[s].saveddata
            else:
                mat = [['field1'], ['none'], ['varchar'], ['']]
                self.tables[s] = Table(self.mast, self.tableframe, 1, None, mat, s, self)
                self.curdata[s] = mat

            self.tablebuttons[s] = tk.Button(self.subbuttonframe, text=s, bg=theme[3], fg=theme[4])
            self.tablebuttons[s].config(command=lambda n=s: self.changetable.open(n))
            self.tablebuttons[s].grid(row=self.tablecount + 3, column=0, sticky='news')
            self.tablecount += 1
            i = 1
            self.subbuttonframe.update_idletasks()
            scroll_region = self.buttoncanvas.bbox('all')
            self.buttoncanvas.configure(scrollregion=scroll_region)
        elif acc == 'xuser':
            self.mast.wuserprompt.open()
        elif acc == 'never':
            self.mast.crucial.open()

    def out_matrix(self):
        if self.active != None:
            self.curdata[self.active] = self.tables[self.active].out_matrix()
        return self.curdata

    def saveself(self, path=None, type=None):
        try:
            self.out_matrix()
            saveddata = self.curdata
            if path == None:
                self.saveddata = saveddata
                path = self.path
                type = self.type
            if type == 'db':
                open(path, 'w')
                db = sql.connect(path)
                cursor = db.cursor()
                for k in list(saveddata.keys()):
                    columns = len(saveddata[k][2])
                    lst = []
                    ext = ''
                    for i in range(len(saveddata[k][0])):
                        for r in range(3):
                            dat = saveddata[k][r][i]
                            if 'foreign key' == dat[:11]:
                                if len(self.saveddata) > 1:
                                    ext += ', ' + dat
                                lst.append('none')
                            else:
                                lst.append(saveddata[k][r][i])
                        lst[i*3+1], lst[i*3+2] = lst[i*3+2], lst[i*3+1]
                    com = 'create table {}(' + ('{} {} {},' * columns).removesuffix(',') + ext + ');'
                    cursor.execute((com).format(k, *lst))
                    for rec in saveddata[k][3:]:
                        if len(rec) == 1:
                            s = str(tuple(rec))[:-2] + ')'
                        else:
                            s = str(tuple(rec))
                        cursor.execute(f'insert into {k} values {s};')
                db.commit()
                db.close()
            else:
                if len(self.tables) == 1:
                    a = MessageBox(self.root, "Only 1 Table",
                                   "This database only has 1 table.\nSaving it as excel will convert it\ninto a table. Continue?",
                                   [('Save', 1), ('Add Empty Table', -1), ('Cancel', 0)]).ask()
                    if a == 1:
                        pass
                    elif a == 0:
                        return
                    else:
                        self.asknewtable(False)
                with pd.ExcelWriter(path, mode='w', engine=self.mast.getengine(path.split('.')[-1])) as writer:
                    for tname in self.tables.keys():
                        newdat = saveddata[tname]
                        df = pd.DataFrame(newdat[1:], columns=newdat[0])
                        df.to_excel(writer, sheet_name=tname, index=False)
            return saveddata
        except:
            a = MessageBox(self.root, 'Saving Error Occurred', 'An unexpected\nerror occurred',
                           [('Okay', 0), ('Retry', 1)]).ask()
            if not a:
                return
            else:
                self.saveself(path, type)

    def savenew(self, path):
        type = path.split('.')[-1].lower()
        if type in ['db'] + excelt:
            savdat = self.saveself(path, type)
        else:
            self.mast.wrongfiletypeprompt.open(f'Cannot save databases as .{type}\ntry Excel or Database types.')
            return
        if self.path == None:
            self.path = path
            self.type = type
            self.saveddata = savdat
            self.root.title(path)

    def changetablelogic(self, name):
        if self.active != None:
            self.tables[self.active].cfpro.exists = True
        n = name[0]
        self.changetable.optionframe = tk.Frame(self.changetable.screen)
        self.changetable.screen.configure(bg=theme[2])

        tk.Label(self.changetable.optionframe, text="Name:", bg=theme[2], fg=theme[0]).grid(row=0, column=0, sticky='news')

        self.changetable.nameentry = tk.Entry(self.changetable.optionframe, fg=theme[0], bg=theme[1], width=16)
        self.changetable.nameentry.insert(0, n)
        self.changetable.nameentry.grid(row=0, column=1, sticky='news')

        tk.Button(self.changetable.optionframe, text="Update", command=lambda: self.rename_table(n), bg=theme[3], fg=theme[4]).grid(row=1, column=0, sticky='news')
        tk.Button(self.changetable.optionframe, text="Delete", command=lambda: self.drop_table(n), bg=theme[3], fg=theme[4]).grid(row=1, column=1, sticky='news')
        tk.Button(self.changetable.screen, text="Open", command=lambda: self.open_table(n), bg=theme[3], fg=theme[4]).pack()

        self.changetable.optionframe.pack()

    def swect(self):
        if self.active != None:
            self.tables[self.active].cfpro.exists = False
        self.changetable.screen.withdraw()

    def open_table(self, name):
        self.changetable.close()
        if self.active != None:
            self.curdata[self.active] = self.tables[self.active].out_matrix()
            for w in self.tableframe.winfo_children():
                w.destroy()
        self.active = name
        self.tables[name].tk_display()

    def rename_table(self, name):
        new = self.changetable.nameentry.get().strip().lower()
        names = [i for i in list(self.curdata.keys())]
        names.remove(name)
        if not checkname(new, names):
            return
        if self.active == name:
            self.active = new
        self.tables[name].name = new
        self.tables[new] = self.tables[name]
        self.tables.pop(name)
        self.curdata[new] = self.curdata[name]
        self.curdata.pop(name)
        self.tablebuttons[name].config(text=new, command=lambda n=new: self.changetable.open(n))
        self.tablebuttons[new] = self.tablebuttons[name]
        self.tablebuttons.pop(name)
        self.changetable.close()

    def drop_table(self, name):
        if self.active == name:
            self.tables[self.active].mainframe.destroy()
            self.active = None
        self.tables.pop(name)
        self.curdata.pop(name)
        self.tablebuttons.pop(name)
        self.tablecount -= 1
        for w in self.buttoncanvas.winfo_children():
            w.destroy()
        self.make_buttons()
        self.changetable.close()


class Table:
    def __init__(self, main, screen, dep=0, path=None, preset=None, name=None, mast=None):
        self.path = path
        self.st = None
        self.main = main
        self.mast = mast
        self.preset = preset
        self.saveddata = []
        self.fields = {}
        self.boxes = {}
        self.rows = 0
        self.columns = 0
        self.dep = dep

        self.cfpro = Prompt(self.changefieldlogic, 0, self.swecf)
        self.cfpro.screen.title("Field Data")

        self.root = screen
        if dep:
            self.name = name
        else:
            if path != None:
                self.root.title(path)
            else:
                self.root.title('Application')
        self.load()

    def tk_display(self):
        self.mainframe = tk.Frame(self.root, bg=theme[2])
        self.mainframe.pack(fill=tk.BOTH, expand=1)
        self.buttonframe = tk.Frame(self.mainframe, bg=theme[2])
        self.addfieldbutton = tk.Button(self.buttonframe, text="Add Field", command=self.add_field, bg=theme[3], fg=theme[4])
        self.addfieldbutton.grid(row=0, column=0)
        self.addrecordbutton = tk.Button(self.buttonframe, text="Add Record", command=self.add_record, bg=theme[3], fg=theme[4])
        self.addrecordbutton.grid(row=0, column=1)
        self.buttonframe.pack()

        self.tablewindow = tk.Frame(self.mainframe, bg=theme[2])
        self.tablewindow.pack(fill=tk.BOTH, expand=1)

        self.canvas = tk.Canvas(self.tablewindow, bg=theme[2])
        self.canvas.grid(row=0, column=0, sticky='news')

        # Add A Scrollbar To The Canvas
        self.scrollbary = ttk.Scrollbar(self.tablewindow, orient=tk.VERTICAL, command=self.canvas.yview)
        self.scrollbary.grid(row=0, column=1, sticky='news')
        self.scrollbarx = ttk.Scrollbar(self.tablewindow, orient=tk.HORIZONTAL, command=self.canvas.xview)
        self.scrollbarx.grid(row=1, column=0, sticky='news')

        self.canvas.configure(xscrollcommand=self.scrollbarx.set, yscrollcommand=self.scrollbary.set)
        self.canvas.bind('<Configure>', lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")))

        self.makeboxes()

        # instead of directly calling self.main.loaderror.open in self.load, which causes Table.__init__() to be
        # interupted, we used a boolean to do this after initializing is done
        if self.olerror:
            self.main.loaderror.open()
            self.olerror = False

    def makeboxes(self):
        self.tableframe = tk.Frame(self.canvas, bg=theme[2])
        self.canvas.create_window((0, 0), window=self.tableframe, anchor="nw")
        self.boxes['none'] = tk.Button(self.tableframe, text='', bg = theme[3], fg=theme[4])
        self.boxes['none'].grid(row=0, column=0, sticky='news')
        self.boxes['none'].config(state=tk.DISABLED)
        for i in range(self.columns):
            self.boxes[f'field{i}'] = tk.Button(self.tableframe, text=self.fields[i].name, bg = theme[3], fg=theme[4])
            self.boxes[f'field{i}'].config(command=lambda i=i: self.cfpro.open(i))
            self.boxes[f'field{i}'].grid(row=0, column=i+1, sticky='news')
        for i in range(self.columns):
            for j in range(self.rows):
                self.boxes[f'entry{j}_{i}'] = tk.Entry(self.tableframe, width=self.fields[i].maxlen + 4, bg = theme[1], fg=theme[0])
                self.boxes[f'entry{j}_{i}'].insert(0, self.fields[i].subdata.get(j, ''))
                self.boxes[f'entry{j}_{i}'].grid(row=j + 1, column=i+1, sticky='news')
        for i in range(self.rows):
            self.boxes[f'remove{i}'] = tk.Button(self.tableframe, text="x", bg = theme[3], fg=theme[4])
            self.boxes[f'remove{i}'].config(command=lambda i=i: self.removerecord(i))
            self.boxes[f'remove{i}'].grid(row=i+1, column=0, sticky='news')
        self.updatescroll()

    def load(self):
        self.olerror = False
        if self.dep == 1:
            self.preset = self.updatevaild(self.preset)
            for rec in self.preset[3:]:
                self.load_record(rec)
            self.saveddata = self.preset
            return
        if self.path == None:
            if self.preset==None:
                self.load_field(0, 'field1')
                self.load_record([''])
                self.saveddata = [['field1'], ['none'], ['varchar'], ['']]
                return
            else:
                self.path = self.preset
        try:
            try:
                with open(self.path, 'rb') as f:
                    mat = pickle.load(f)
                self.st = 'bin'
            except:
                try:
                    with pd.ExcelFile(self.path) as d:
                        tname = d.sheet_names[0]
                        raw = pd.DataFrame(pd.read_excel(d, sheet_name=tname))
                        raw.replace(numpy.nan, '', inplace=True)
                        mat = [list(raw.keys())]
                        for r in raw.values:
                            mat.append(list(r))
                    self.st = 'excel'
                except:
                    with open(self.path) as f:
                        reader = csv.reader(f)
                        mat = []
                        for row in reader:
                            if len(row):
                                mat.append(row)
                    self.st = 'csv'

            mat = self.updatevaild(mat)

            for rec in mat[3:]:
                self.load_record(rec)
            self.saveddata = mat
        except:
            self.rows = 0
            self.columns = 0
            self.load_field(0, 'field1')
            self.load_record([''])
            self.saveddata = [['field1'], ['none'], ['varchar'], ['']]
            self.st = 'csv'
            self.olerror = True

    def updatevaild(self, mat):
        # Starting to check data validity and changing the data if it is not
        tc = len(mat[0])
        try:
            mat[1]
        except IndexError:
            mat.append(['none'] * tc)
            self.olerror = True
        try:
            mat[2]
        except IndexError:
            mat.append(['varchar'] * tc)
            self.olerror = True

        check = any(t.lower() in typelist for t in mat[2])
        if not any(c.lower() in conslist or c[:7].lower() == 'default' for c in mat[1]):
            self.olerror = True
            mat.insert(1, ['none'] * tc)
            if check:
                mat[2], mat[3] = mat[3], mat[2]
        if not check and not any(t.lower() in typelist for t in mat[2]):
            self.olerror = True
            mat.insert(2, ['none'] * tc)

        names = []
        for k in range(len(mat[0])):
            f = str(mat[0][k]).strip().lower()
            skipn = False
            tr = 'field1'
            for i in range(1):
                if not len(f):
                    break
                n = f.split()
                if n[0] == 'default':
                    break
                if len(n) > 1:
                    tr = n[0]
                    break
                if not checkname(f, names):
                    break
                skipn = True
            if skipn:
                names.append(f)
                continue
            # Reason behind using a while loop over index is if a name field{i} already exists, it would be repeated
            while True:
                if tr not in names:
                    break
                i += 1
                tr = f'field{i}'
            self.olerror = True
            names.append(tr)
        mat[0] = names
        for ri in range(len(mat)):
            cc = len(mat[ri])
            if cc != tc:
                self.olerror = True
                mat[ri].extend([''] * (tc - cc))
            if ri == 1:
                for c in range(len(mat[1])):
                    con = str(mat[1][c]).split()
                    if con[0].lower() == 'default':
                        con[0] = con[0].lower()
                    else:
                        con = [st.lower() for st in con]
                    mat[ri][c] = ' '.join(con)
            elif ri == 2:
                mat[2] = [str(e).strip().lower() for e in mat[2]][:tc]
            else:
                mat[ri] = [str(e).strip() for e in mat[ri]][:tc]

        self.has_pri = False
        for i in range(tc):
            for j in range(1):
                c = mat[1][i].split()
                if not len(c):
                    mat[1][i] = 'none'
                    self.olerror = True
                    break
                if mat[1][i] == 'primary key' and not self.has_pri:
                    self.has_pri = True
                elif mat[1][i] == 'primary key':
                    mat[1][i] = 'none'
                    self.olerror = True
                    break
                if mat[1][i][:11] == 'foreign key' and not self.dep:
                    mat[1][i] = 'none'
                    self.olerror = True
                    break
                if c[0] == 'default':
                    if len(c) == 1:
                        mat[1][i] = 'default pickdef'
                        self.olerror = True
                        c.append('pickdef')
                    for k in range(3, len(mat)):
                        if not len(mat[k][i]):
                            mat[k][i] = c[1].strip()
                    break
                elif mat[1][i] in conslist:
                    break
                mat[1][i] = 'none'
                self.olerror = True
            for j in range(1):
                if mat[2][i] in typelist:
                    break
                else:
                    mat[2][i] = 'varchar'
                    self.olerror = True
            self.load_field(i, mat[0][i], mat[2][i], mat[1][i])
        # End of validity check
        return mat

    def saveself(self):
        try:
            if self.path == None:
                return
            newdat = self.out_matrix()
            if self.st == 'csv':
                with open(self.path, 'w') as f:
                    writer = csv.writer(f)
                    writer.writerows(newdat)
            elif self.st == 'bin':
                with open(self.path, 'wb') as f:
                    pickle.dump(newdat, f)
            elif self.st == 'excel':
                d = pd.ExcelFile(self.path)
                tname = d.sheet_names[0]
                df = pd.DataFrame(newdat[1:], columns=newdat[0])
                with pd.ExcelWriter(self.path, mode='w', engine=self.main.getengine(self.path.split('.')[-1])) as writer:
                    df.to_excel(writer, sheet_name=tname, index=False)
                d.close()
            self.saveddata = newdat
        except:
            a = MessageBox(self.root, 'Saving Error Occurred', 'An unexpected\nerror occurred', [('Okay', 0), ('Retry', 1)]).ask()
            if not a:
                return
            else:
                self.saveself()

    def savenew(self, path):
        try:
            type = path.split('.')[-1].lower()
            newdat = self.out_matrix()
            if type in tablet[:-1]:
                with open(path, 'w') as f:
                    writer = csv.writer(f)
                    writer.writerows(newdat)
            elif type == 'dat':
                with open(path, 'wb') as f:
                    pickle.dump(newdat, f)
            elif type in excelt:
                df = pd.DataFrame(newdat[1:], columns=newdat[0])
                with pd.ExcelWriter(path, mode='w', engine=self.main.getengine(path.split('.')[-1])) as writer:
                    df.to_excel(writer, sheet_name='Table', index=False)
            else:
                self.main.wrongfiletypeprompt.open(f'Cannot save tables as .{type}\ntry Excel or Table types.')
        except:
            a = MessageBox(self.root, 'Saving Error Occurred', 'An unexpected\nerror occurred', [('Okay', 0), ('Retry', 1)]).ask()
            if not a:
                return
            else:
                self.savenew(path)
            return
        if self.path == None:
            self.path = path
            self.root.title(path)
            self.saveddata = newdat

    def out_matrix(self):
        c = []
        t = []
        n = []
        for j in range(self.columns):
            if self.fields[j].constraint == 'default':
                c.append('default ' + self.fields[j].defval)
            elif self.fields[j].constraint == 'foreign key':
                c.append(f'foreign key ({self.fields[j].name}) references {self.fields[j].mtable}({self.fields[j].rfield})')
            else:
                c.append(self.fields[j].constraint)
            t.append(self.fields[j].type)
            n.append(self.fields[j].name)
        mat = [n,c,t]
        for i in range(self.rows):
            row = []
            for j in range(self.columns):
                e = self.boxes[f'entry{i}_{j}'].get().strip()
                row.append(e)
                self.fields[j].subdata[i] = e
            mat.append(row)
        return mat

    def load_field(self, index, name, type='varchar', constraint="none"):
        if name in self.fields.keys():
            fieldnames = []
            for k in range(self.columns):
                fieldnames.append(self.fields[k].name)
            i = 1
            while True:
                if f'field{i}' not in fieldnames:
                    name = f'field{i}'
                    break
                i += 1
        self.fields[index] = Field(index, name, type, constraint)
        self.columns += 1

    def load_record(self, rec):
        for i in range(self.columns):
            self.fields[i].subdata[self.rows] = rec[i]
        self.rows += 1

    def add_field(self):
        fieldnames = []
        for k in range(self.columns):
            fieldnames.append(self.fields[k].name)
        i = 1
        while True:
            if f'field{i}' not in fieldnames:
                k = self.columns
                self.load_field(self.columns, f'field{i}')
                break
            i += 1
        for i in range(self.rows):
            self.fields[k].subdata[i] = ''
        self.boxes[f'field{k}'] = tk.Button(self.tableframe, text=self.fields[k].name, bg = theme[3], fg=theme[4])
        self.boxes[f'field{k}'].config(command=lambda i=k: self.cfpro.open(i))
        self.boxes[f'field{k}'].grid(row=0, column=k+1, sticky='news')
        for j in range(self.rows):
            self.boxes[f'entry{j}_{k}'] = tk.Entry(self.tableframe, width=self.fields[k].maxlen + 4, bg = theme[1], fg=theme[0])
            self.boxes[f'entry{j}_{k}'].insert(0, '')
            self.boxes[f'entry{j}_{k}'].grid(row=j + 1, column=k+1, sticky='news')
        self.updatescroll()

    def add_record(self):
        k = self.rows
        for j in range(self.columns):
            self.fields[j].subdata[k] = ''
            self.boxes[f'entry{k}_{j}'] = tk.Entry(self.tableframe, width=self.fields[j].maxlen + 4, fg=theme[0], bg=theme[1])
            if self.fields[j].constraint == 'default':
                self.boxes[f'entry{k}_{j}'].insert(0, self.fields[j].defval)
            else:
                self.boxes[f'entry{k}_{j}'].insert(0, '')
            self.boxes[f'entry{k}_{j}'].grid(row=k+1, column=j+1, sticky='news')
        self.boxes[f'remove{k}'] = tk.Button(self.tableframe, text="x", bg = theme[3], fg=theme[4])
        self.boxes[f'remove{k}'].config(command=lambda i=k: self.removerecord(i))
        self.boxes[f'remove{k}'].grid(row=k + 1, column=0, sticky='news')
        self.rows +=1
        self.updatescroll()

    def changefieldlogic(self, index):
        i = index[0]
        self.cfpro.optionframe = tk.Frame(self.cfpro.screen)
        self.cfpro.screen.configure(bg=theme[2])

        self.cflabels = {}
        self.cflabels['name'] = tk.Label(self.cfpro.optionframe, text="Name:", bg=theme[2], fg=theme[0])
        self.cflabels['type'] = tk.Label(self.cfpro.optionframe, text="Type:", bg=theme[2], fg=theme[0])
        self.cflabels['cons'] = tk.Label(self.cfpro.optionframe, text="Constaint:", bg=theme[2], fg=theme[0])
        self.cflabels['def'] = tk.Label(self.cfpro.optionframe, text="Default:", bg=theme[2], fg=theme[0])
        self.cflabels['tab'] = tk.Label(self.cfpro.optionframe, text="Parent:", bg=theme[2], fg=theme[0])
        self.cflabels['fie'] = tk.Label(self.cfpro.optionframe, text="Field:", bg=theme[2], fg=theme[0])

        self.cfbuttons = {}
        self.cfbuttons['chan'] = tk.Button(self.cfpro.optionframe, text="Change",
                                           command=lambda: self.changefielddata(i), bg=theme[3], fg=theme[4])
        self.cfbuttons['rem'] = tk.Button(self.cfpro.optionframe, text="Remove", command=lambda: self.removefield(i),
                                          bg=theme[3], fg=theme[4])

        self.cfpro.nameentry = tk.Entry(self.cfpro.optionframe, fg=theme[0], bg=theme[1], width=16)
        self.cfpro.nameentry.insert(0, self.fields[i].name)

        self.cfpro.defentry = tk.Entry(self.cfpro.optionframe, fg=theme[0], bg=theme[1], width=16)
        self.cfpro.defentry.insert(0, self.fields[i].defval)

        self.cfpro.typechoice = tk.StringVar()
        self.cfpro.typechoice.set(self.fields[i].type)
        self.cfpro.typemenu = tk.OptionMenu(self.cfpro.optionframe, self.cfpro.typechoice, *typelist)
        self.cfpro.typemenu.config(fg=theme[0], bg=theme[1])

        if self.dep:
            self.mast.changetable.exists = True
            self.mast.allowfor = True
            self.peers = self.mast.out_matrix()
            self.peers.pop(self.name)
            names = list(self.peers.keys())
            try:
                if len(self.fields[i].mtable):
                    dt = self.fields[i].mtable
                else:
                    dt = names[0]
            except AttributeError:
                dt = names[0]
            except IndexError:
                self.mast.allowfor = False
                dt = 0
            else:
                self.cfpro.ptab = tk.StringVar()
                self.cfpro.ptab.set(dt)
                self.cfpro.ptabmenu = tk.OptionMenu(self.cfpro.optionframe, self.cfpro.ptab, *names)
                self.cfpro.ptabmenu.config(fg=theme[0], bg=theme[1])
                self.cfpro.ptab.trace_add('write', self.refreshrfield)

            try:
                if len(self.fields[i].rfield):
                    df = self.fields[i].rfield
                else:
                    df = self.peers[dt][0][0]
            except AttributeError:
                df = self.peers[dt][0][0]
            except KeyError:
                self.mast.allowfor = False
            else:
                self.cfpro.rfie = tk.StringVar()
                self.cfpro.rfie.set(df)
                self.cfpro.rfiemenu = tk.OptionMenu(self.cfpro.optionframe, self.cfpro.rfie, *self.peers[names[0]][0])
                self.cfpro.rfiemenu.config(fg=theme[0], bg=theme[1])

        self.cfpro.conschoice = tk.StringVar()
        self.cfpro.conschoice.set(self.fields[i].constraint)
        self.cfpro.consmenu = tk.OptionMenu(self.cfpro.optionframe, self.cfpro.conschoice, *conslist)
        self.cfpro.consmenu.config(fg=theme[0], bg=theme[1])
        self.cfpro.conschoice.trace_add('write', self.updatecfs)
        if self.dep and not self.mast.allowfor:
            self.fields[i].constraint = 'none'
            self.cfpro.conschoice.set('none')
            self.cfpro.consmenu['menu'].entryconfig('foreign key', state=tk.DISABLED)

        self.updatecfs()

    def swecf(self):
        if self.dep:
            self.mast.changetable.exists = False
        self.cfpro.screen.withdraw()

    def updatecfs(self, *args):
        self.cfpro.optionframe.pack_forget()
        for w in self.cfpro.optionframe.winfo_children():
            w.grid_forget()
        opt = self.cfpro.conschoice.get()
        self.cflabels['name'].grid(row=0, column=0, sticky='news')
        self.cflabels['type'].grid(row=1, column=0, sticky='news')
        self.cflabels['cons'].grid(row=2, column=0, sticky='news')
        self.cfpro.nameentry.grid(row=0, column=1, sticky='news')
        self.cfpro.typemenu.grid(row=1, column=1, sticky='news')
        self.cfpro.consmenu.grid(row=2, column=1, sticky='news')
        if opt == 'default':
            self.cflabels['def'].grid(row=3, column=0, sticky='news')
            self.cfpro.defentry.grid(row=3, column=1, sticky='news')
            self.cfbuttons['chan'].grid(row=4, column=0, sticky='news')
            self.cfbuttons['rem'].grid(row=4, column=1, sticky='news')
            self.cfpro.optionframe.pack()
        elif opt == 'foreign key':
            self.cflabels['tab'].grid(row=3, column=0, sticky='news')
            self.cflabels['fie'].grid(row=4, column=0, sticky='news')
            self.cfpro.ptabmenu.grid(row=3, column=1, sticky='news')
            self.cfpro.rfiemenu.grid(row=4, column=1, sticky='news')
            self.cfbuttons['chan'].grid(row=5, column=0, sticky='news')
            self.cfbuttons['rem'].grid(row=5, column=1, sticky='news')
            self.cfpro.optionframe.pack()
        else:
            self.cfbuttons['chan'].grid(row=3, column=0, sticky='news')
            self.cfbuttons['rem'].grid(row=3, column=1, sticky='news')
            self.cfpro.optionframe.pack()

    def refreshrfield(self, *args):
        tab = self.cfpro.ptab.get()
        new = self.peers[tab][2]
        self.cfpro.rfiemenu['menu'].delete(0, tk.END)
        self.cfpro.rfie.set(new[0])
        for f in new:
            self.cfpro.rfiemenu['menu'].add_command(label=f, command=lambda f=f:self.cfpro.rfie.set(f))

    def changefielddata(self, i):
        newname = self.cfpro.nameentry.get().strip().lower()
        names = [self.fields[i].name for i in range(self.columns)]
        names.remove(self.fields[i].name)
        if not checkname(newname, names):
            return
        self.fields[i].name = newname
        self.fields[i].type = self.cfpro.typechoice.get()
        cons = self.cfpro.conschoice.get()
        dev = self.cfpro.defentry.get().strip()
        if cons == 'default' and len(dev) == 0:
            self.main.emptydefault.open()
            return
        if cons == 'primary key' and self.has_pri:
            self.main.multipri.open()
            return
        elif cons == 'primary key':
            self.has_pri = True
        if cons == 'foreign key':
            tab = self.cfpro.ptab.get()
            fie = self.cfpro.rfie.get()
            self.fields[i].mtable = tab
            self.fields[i].rfield = fie
        if cons != 'primary key' and self.fields[i].constraint == 'primary key':
            self.has_pri = False
        self.fields[i].constraint = cons
        self.fields[i].defval = dev
        self.boxes[f'field{i}'].config(text=self.fields[i].name)
        self.cfpro.close()

    def removefield(self, index):
        self.cfpro.close()
        new = {}
        for i in self.fields:
            if i>index:
                new[i-1]=self.fields[i]
            if i<index:
                new[i] = self.fields[i]
        self.fields = new
        self.columns -= 1
        self.out_matrix()
        self.tableframe.destroy()
        self.boxes = {}
        self.makeboxes()

    def removerecord(self, index):
        self.out_matrix()
        for i in range(self.columns):
            self.fields[i].subdata.pop(index)
        for i in range(self.rows):
            if i>index:
                for j in range(self.columns):
                    self.fields[j].subdata[i-1] = self.fields[j].subdata[i]
        self.rows -= 1
        self.tableframe.destroy()
        self.boxes = {}
        self.makeboxes()

    def updatescroll(self):
        self.tableframe.update_idletasks()
        scroll_region = self.canvas.bbox('all')
        self.canvas.configure(scrollregion=scroll_region)


class Field:
    def __init__(self, index, name, type='varchar', constraint="none"):
        self.name = name.lower()
        c = constraint.split()
        if 'default' == c[0]:
            self.constraint = 'default'
            self.defval = ' '.join(c[1:])
        elif ['foreign', 'key'] == c[:2]:
            self.constraint = 'foreign key'
            t = c[-1].split('(')
            self.mtable = t[0].strip()
            self.rfield = t[1].strip().removesuffix(')').rstrip()
        else:
            self.constraint = constraint
            self.defval = ''
            self.mtable = ''
            self.rfield = ''
        self.type = type
        self.subdata = {}
        self.maxlen = 5

    def newmaxlen(self):
        for rec in list(self.subdata.values()):
            if len(str(rec)) > self.maxlen:
                self.maxlen = len(str(rec))


class SQL:
    def __init__(self, screen, path, user=None):
        self.root = screen
        self.user = user
        self.path = path
        self.changed0 = False
        self.changed = False
        self.root.title(self.path)
        self.db = sql.connect(self.path)
        self.cursor = self.db.cursor()

    def tk_display(self):
        self.mainframe = tk.Frame(self.root, bg=theme[2])

        self.buttonframe = tk.Frame(self.mainframe, bg=theme[2])
        self.enterbutton = tk.Button(self.buttonframe, text='Enter', bg=theme[3], fg=theme[4], command=self.execute)
        self.savebutton = tk.Button(self.buttonframe, text='Save Changes', bg=theme[3], fg=theme[4], command=self.saveself)

        self.enterbutton.grid(row=0, column=0, sticky='news')
        self.savebutton.grid(row=0, column=1, sticky='news')

        self.comentry = tk.Entry(self.mainframe, fg=theme[0], bg=theme[1], width=35)
        self.tbox = tk.Text(self.mainframe, fg=theme[0], bg=theme[1])
        self.mainframe.pack(fill=tk.BOTH, expand=1)
        self.buttonframe.grid(row=0, column=0, sticky='news')
        self.comentry.grid(row=1, column=0, sticky='news')
        self.tbox.grid(row=2, column=0)

        self.tbox.config(state=tk.DISABLED)

    def execute(self):
        self.changed0 = self.changed
        self.tbox.config(state=tk.NORMAL)
        command = self.comentry.get().strip()
        if len(command) == 0:
            return
        self.tbox.insert(tk.END, f'>>> {command}\n')
        try:
            if command.lower().removesuffix(';') == 'show tables':
                ret = [i[1] for i in self.cursor.execute('select * from sqlite_schema;').fetchall()]
                for l in ret:
                    self.tbox.insert(tk.END, l+'\n')
            elif command[:12] == 'insert into ':
                self.cursor.execute(command)
                t = command.split()
                tname = t[2].split('(')[0]
                for i in self.cursor.execute(f'pragma table_info({tname})'):
                    if i[5]:
                        cname = i[1]
                        break
                # insert into a(class) values(10)
                ret = self.cursor.execute(f'select {cname} from {tname}').fetchall()
                if any(z[0] == None for z in ret):
                    self.cursor.execute(f'delete from {tname} where {cname} is Null')
                    raise EmptyEntry
            else:
                ret = self.cursor.execute(command).fetchall()
                for l in ret:
                    self.tbox.insert(tk.END, '  ,  '.join([str(i) for i in l])+'\n')
            self.tbox.insert(tk.END, '>>> Command successfully executed\n')
            self.comentry.delete(0, tk.END)
            st = command.split()[0].lower()
            if st != 'select' and st != 'show':
                self.changed = True
        except EmptyEntry:
            self.tbox.insert(tk.END, '>>> No value was given for primary key. Try again. \n')
            self.changed = self.changed0
        except sql.IntegrityError as ex:
            mes = ex.args[0]
            self.changed = self.changed0
            if mes[:26] == 'NOT NULL constraint failed':
                self.tbox.insert(tk.END, f">>> No value was given for field '{mes[30:]}'. Try again. \n")
            else:
                print('add new:')
                print(mes)
        except sql.OperationalError as ex:
            self.changed = self.changed0
            mes = ex.args[0]
            print(mes)
            raise IndexError
        except:
            self.changed = self.changed0
            self.tbox.insert(tk.END, '>>> An error occured. Try rephrasing your command. \n')
        self.tbox.config(state=tk.DISABLED)

    def saveself(self):
        self.db.commit()
        self.changed = False


class Prompt:
    active = []
    def __init__(self, func=lambda: None, uptime=10, closefunc=0):
        self.exists = False
        self.uptime = uptime*1000
        self.action = func
        self.closef = closefunc
        self.screen = tk.Toplevel()
        self.screen.resizable(0, 0)
        self.screen.protocol("WM_DELETE_WINDOW", self.close)
        self.screen.withdraw()

    def open(self, *args):
        Prompt.active.append(self)
        if self.exists:
            return
        self.exists = True
        self.screen.deiconify()
        self.screen.attributes('-topmost', True)
        if len(args) != 0:
            self.action(args)
        else:
            self.action()
        if self.uptime:
            self.stopseq = self.screen.after(self.uptime, self.close)

    def close(self):
        if self in Prompt.active:
            Prompt.active.remove(self)
        self.exists = False
        for w in self.screen.winfo_children():
            w.pack_forget()
        if self.uptime:
            self.screen.after_cancel(self.stopseq)
        if self.closef != 0:
            self.closef()
        else:
            self.screen.withdraw()

# We are using a custom messagebox class as tkinter.messagebox does not allow customization of options
class MessageBox(Prompt):
    def __init__(self, root, title, message, buttons):
        super().__init__(self.action, 0, lambda :self.ret(0))
        self.screen.title(title)
        self.screen.config(bg=theme[2])
        self.root = root
        self.message = message
        self.b = buttons
        self.answer = tk.IntVar()

    def action(self):
        Prompt.active.remove(self)
        self.messagelab = tk.Label(self.screen, text=self.message, bg=theme[2], fg=theme[5])
        self.buttonframe = tk.Frame(self.screen)
        for i in range(len(self.b)):
            tk.Button(self.buttonframe, text=self.b[i][0], command=lambda i=i: self.ret(self.b[i][1]), fg=theme[4],bg=theme[3]).grid(row=0, column=i, sticky='news')
        self.messagelab.pack()
        self.buttonframe.pack()
        self.screen.grab_set()

    def ask(self):
        self.answer.set(0)
        self.open()
        self.root.wait_variable(self.answer)
        return self.answer.get()

    def ret(self, val):
        self.answer.set(val)
        self.screen.grab_release()
        self.screen.destroy()


def opensetmast():
    global usent, psent, setmast
    setmast = tk.Tk()
    setmast.protocol("WM_DELETE_WINDOW", lambda: None)
    setmast.resizable(0, 0)
    tkFont.nametofont("TkDefaultFont").configure(family='Calibri', size=18)
    tkFont.nametofont("TkTextFont").configure(family='Calibri', size=18)
    setmast.configure(bg=theme[2])
    setmast.title("Enter Details")
    tk.Label(setmast, text='Master Username:', bg=theme[2], fg=theme[0]).pack()
    usent = tk.Entry(setmast, bg=theme[1], fg=theme[0])
    usent.pack(padx=20)
    tk.Label(setmast, text='Master Password:', bg=theme[2], fg=theme[0]).pack()
    psent = tk.Entry(setmast, bg=theme[1], fg=theme[0])
    psent.pack(padx=20)
    tk.Button(setmast, text='Enter', command=cmaster, bg=theme[3],
              fg=theme[4]).pack(pady=10)
    setmast.mainloop()

def cmaster():
    global usent,psent,setmast
    u = usent.get().strip()
    p = psent.get().strip()
    if len(u) == 0 or len(p) == 0:
        return
    with open('AppData/pass.dat', 'wb') as f:
        os.mkdir(f'AppData/User {u}' )
        os.mkdir(f'AppData/User {u}/Presets' )
        pickle.dump([u, p], f)
    setmast.destroy()

def checkcol(col):
    cons = col[1]
    type = col[2]
    dat = col[3:]
    if type == 'integer':
        for e in dat:
            e = str(e)
            if e.isdigit() or not len(e):
                continue
            else:
                raise WrongDataType
    elif type == 'none':
        raise UndefType
    if cons in 'primary key unique':
        count = {}
        for i in dat:
            if i not in count:
                count[i] = 1
            else:
                raise NotUnique
    if cons in 'primary key not null':
        for e in dat:
            e = str(e)
            if len(e)==0:
                raise EmptyEntry
    if 'foreign key' in cons:
        raise ForeignKeyInteg

def hor_to_vert(mat):
    e = []
    for i in range(len(mat[0])):
        c = []
        for n in range(len(mat)):
            c.append(mat[n][i])
        e.append(c)
    return e

def checkname(name, set=[]):
    if len(name.split()) != 1:
        return 0
    if name in conslist + typelist + set + transres:
        return 0
    if name[0] in bannedstart:
        return 0
    if any(c in name for c in bannedchar):
        return 0
    return 1


typelist = ['varchar', 'char', 'integer', 'date', 'number']
conslist = ['primary key', 'foreign key', 'unique', 'default', 'not null', 'none']
excelf = '.xls .xlsx .xlsm .xlsb .ods'
excelt = ['xls', 'xlsx', 'xlsm', 'xlsb', 'ods']
tablef = '.csv .txt .dat'
tablet = ['csv', 'txt', 'dat']
filetypes = [('Table', tablef),
             ('Database', '.db'),
             ('Excel', excelf),
             ('Show all', '.*')]
bannedchar = "'\"=+-!#?/><.,(){}[]| \\ &*:;~`%^"
bannedstart = ['@', '$'] + [str(i) for i in range(10)]
transres = ['select', 'null', 'insert', 'create', 'sum']
empty = ['none', 'null', '']
# txt on bg, fg, bg, button colour, alert
Dark = ['#ffffff', '#52575a', '#2b2d2e', '#1a1a1a', '#ffffff', '#ff0000']
Light = ['#17191a', '#dbdbde', '#c3c3c3', '#a6a6a6', '#17191a', '#ff0000']
Violet = ['#0e0026', '#b990ff', '#5b00ff', '#2e027b', '#cbb9ea', '#ff0000']
Matte = ['#222222', '#ffffff', '#bfbfbf', '#bfbfbf', '#222222', '#ff0000']
themes = {'Dark':Dark, 'Light':Light, 'Violet':Violet}
theme = Dark

MainScreen()

# TO DO LIST:
# check all excel filetypes
# make frames expand to the size of the screen only and always
# do something with datatypes, constraints like foreign keys, date
# add some themes and default presets
# update SQL transaction keywords
