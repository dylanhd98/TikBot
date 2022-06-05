import os
import praw
import shutil
import pytube
import random
import asyncio
import warnings
import edge_tts
import datetime
import moviepy.editor as mpe
from moviepy.editor import *
from PIL import Image, ImageFont, ImageDraw

#general stuff like first time setup etc
class UtilityHandler:
    def cleanFiles(self):
        if os.path.exists("tempFiles"):
            shutil.rmtree("tempFiles")
        if not os.path.exists("bgFootage"):
            os.mkdir("bgFootage")
        os.mkdir("tempFiles")
        os.mkdir("tempFiles/audio")

    def firstTimeSetup(self):
        os.system('cls' if os.name == 'nt' else 'clear')
        creds = open("praw.ini","w")

        print("""In order to get posts from reddit you must first have 3 pieces of information:
        1. Client ID - The OAuth client ID associated with your registered Reddit application

        2. Client Secret - The OAuth client secret associated with your registered Reddit application

        3. User agent - a unique identifier

        to get this information follow the instructions here : https://github.com/reddit-archive/reddit/wiki/OAuth2
""")
        clID = input("Client ID\n>")
        clSE = input("Client Secret\n>")
        agent = input("User Agent\n>")

        creds.write(f"[bot]\nclient_id={clID}\nclient_secret={clSE}\nuser_agent={agent}")
        creds.close()
        
#creating the videos
class EditHandler:
    def __init__(self):
        self.v = VideoHandler()

    def postFromSort(self,reddit,sub,postNo,commentNo,sort,time):
        submissions = reddit.subreddit(sub)#hot new top rising

        if sort == "hot":
            submissions = submissions.hot(limit = postNo)
        elif sort == "new":
            submissions = submissions.new(limit = postNo)
        elif sort == "rising":
            submissions = submissions.rising(limit = postNo)
        else:
            submissions = submissions.top(time_filter = time,limit = postNo)
        
        clips = []
        for submission in submissions:
            if len(submission.selftext)<3000:
                clips.append(self.v.genPostClip(submission,commentNo))
            else:
                print("POST TEXT TOO LARGE")
        return concatenate_videoclips(clips,method="chain")


    def postFromIds(self,reddit,idArray,commentNo):
        clips = []
        for n in range(len(idArray)):
            clips.append(self.v.genPostClip(reddit.submission(idArray[n]),commentNo))
        return concatenate_videoclips(clips,method="chain")


    def greenScreen(self,clip,bgPath):
        bg = VideoFileClip(bgPath)
        masked_clip = clip.fx(mpe.vfx.mask_color, color=[0, 0, 255], s=2,thr = 25)
        masked_clip = masked_clip.set_pos('center')
        randStart = random.randint(0,int(bg.duration-masked_clip.duration))
        bg = bg.subclip(randStart,randStart+masked_clip.duration)
        final_clip = mpe.CompositeVideoClip([bg,masked_clip]).set_duration(clip.duration)
        return final_clip

#class for generating clips and assembling them
class VideoHandler:
    def __init__(self):
        self.audioCount = 0
        self.screen = ScreenShotHandler()
        self.speech = SpeechHandler()

        
        #all voices
        #self.voices = ["en-CA-ClaraNeural","en-CA-LiamNeural","en-AU-WilliamNeural","en-AU-NatashaNeural","en-NZ-MitchellNeural","en-NZ-MollyNeural","en-GB-LibbyNeural","en-GB-SoniaNeural","en-GB-RyanNeural","en-US-AmberNeural","en-US-AriaNeural","en-US-AshleyNeural","en-US-CoraNeural","en-US-ElizabethNeural","en-US-JennyNeural","en-US-MichelleNeural","en-US-MonicaNeural","en-US-SaraNeural","en-US-BrandonNeural","en-US-ChristopherNeural","en-US-GuyNeural","en-US-EricNeural"]


        # only the good ones
        self.voices = ["en-CA-ClaraNeural","en-AU-NatashaNeural","en-NZ-MollyNeural","en-GB-LibbyNeural","en-GB-SoniaNeural","en-US-AmberNeural","en-US-AriaNeural","en-US-CoraNeural","en-US-ElizabethNeural","en-US-MichelleNeural","en-US-MonicaNeural","en-US-BrandonNeural","en-US-ChristopherNeural","en-US-EricNeural"]

    def genPost(self,submission):
        clip = ColorClip(size=(1080, 1920), color=[0, 0, 255])
        voice = random.choice(self.voices)
        self.screen.genPost(submission,voice)
        self.speech.genPost(submission,f"tempFiles/audio/temp{self.audioCount}-{voice}.wav",voice)

        img = ImageClip("tempFiles/temp.png")
        ado = AudioFileClip(f"tempFiles/audio/temp{self.audioCount}-{voice}.wav")
        self.audioCount += 1

        clip = clip.set_audio(ado)
        clip = clip.set_duration(ado.duration)
        clip = clip.set_fps(10)

        scaleNoise = random.random() *0.2
        img = img.set_pos('center').fx(vfx.resize, 1.2-scaleNoise)

        clip = CompositeVideoClip([clip, img.set_start(0).set_duration(ado.duration)])
        return clip

    def genComment(self,comment):
        clip = ColorClip(size=(1080, 1920), color=[0, 0, 255])
        voice = random.choice(self.voices)
        self.screen.genComment(comment,voice)
        self.speech.genComment(comment,f"tempFiles/audio/temp{self.audioCount}-{voice}.wav",voice)

        img = ImageClip("tempFiles/temp.png")
        ado = AudioFileClip(f"tempFiles/audio/temp{self.audioCount}-{voice}.wav")
        self.audioCount +=1

        clip = clip.set_audio(ado)
        clip = clip.set_duration(ado.duration)
        clip = clip.set_fps(10)

        scaleNoise = random.random()*0.2
        img = img.set_pos('center').fx(vfx.resize, 1.2-scaleNoise)
        clip = CompositeVideoClip([clip, img.set_start(0).set_duration(ado.duration)])

        return clip

    def genPostClip(self,submission,commentNo):
        videos = []

        videos.append(self.genPost(submission))
        
        for com in range(commentNo):
            try:
                comment = submission.comments[com]
                if len(comment.body)<3000:
                    videos.append(self.genComment(comment))
                else:
                    print("COMMENT BODY TOO LONG, SKIPPING")
                    com -=1
            except:
                break

        clip = concatenate_videoclips(videos,method="chain").set_fps(10)
        return clip

#handles tts stuff
class SpeechHandler:
    def __init__(self):
        pass

    async def aSpeak(self,string, path,voice):
        communicate = edge_tts.Communicate()   
        with open(path, "wb") as f:
            async for i in communicate.run(string,voice=voice):
                if i[2] is not None:
                    f.write(i[2])

    def speak(self,string,path,voice):
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            asyncio.get_event_loop().run_until_complete(self.aSpeak(string,path,voice))

    def genPost(self,submission,path,voice):
        msg = str(submission.title)+"..."+str(submission.selftext)
        self.speak(msg,path,voice)

    def genComment(self,comment,path,voice):
        msg = str(comment.body)
        self.speak(msg,path,voice)


#todo: redo all this eventually
#generates realistic looking screenshots from raw text
class ScreenShotHandler:
    def __init__(self):
        #colors
        self.redditBG = (26,26,27)
        self.redditText = (211,214,218)
        self.redditTextFaded = (113,115,116)
        #font and sizes :)
        self.redditFont = ImageFont.truetype("font/NotoSans-Regular.ttf",32)
        self.redditFontSmall = ImageFont.truetype("font/NotoSans-Regular.ttf",23)
        self.redditFontBold = ImageFont.truetype("font/NotoSans-Bold.ttf",32)
        self.redditFontBoldSmall = ImageFont.truetype("font/NotoSans-Bold.ttf",23)
        self.maxWidth = 850 #max width in px of screenshot

    def genComment(self,comment,v):
        img = Image.new('RGB', (self.maxWidth, 10000), self.redditBG)
        draw = ImageDraw.Draw(img)
        draw.text((10,10),str(comment.author)+v,font = self.redditFontBoldSmall)
        crop = self.draw_multiple_line_text(img,str(comment.body),self.redditFont,self.redditText,10,35) + 10
        w,h = img.size
        im2 = img.crop((0,0,w,crop))
        im2.save(f"tempFiles/temp.png")

    def genPost(self,submission,v):
        img = Image.new('RGB', (self.maxWidth, 1000), self.redditBG)
        draw = ImageDraw.Draw(img)
        draw.text((10, 5), "r/"+str(submission.subreddit), font=self.redditFontBoldSmall)
        #draw.text(((len(str(submission.subreddit))*13)+30, 5), " • Posted by u/"+str(submission.author)+v,font=self.redditFontSmall,fill = self.redditTextFaded)
        draw.text(((len(str(submission.subreddit))*13)+30, 5), " • Posted by u/"+str(submission.author),font=self.redditFontSmall,fill = self.redditTextFaded)
        titleStop = self.draw_multiple_line_text(img, str(submission.title), self.redditFontBold, self.redditText, 10, 35)
        crop = self.draw_multiple_line_text(img, str(submission.selftext), self.redditFontSmall, self.redditText, 10, 10+ titleStop) + 10
        w, h = img.size
        im2 = img.crop((0, 0, w, crop))
        im2.save(f"tempFiles/temp.png")

    def timeSince(self,timeStamp):#todo display "posted 5hrs. ago" etc
        span = (datetime.datetime.utcnow()-datetime.datetime.utcfromtimestamp(timeStamp))
        return str(span)

    def draw_multiple_line_text(self,image, text, font, text_color, textX,textY):
        draw = ImageDraw.Draw(image)
        y_text = textY
        lines = self.textWrap(text,font)
        for line in lines:
            line_width, line_height = font.getsize(line)
            draw.text((textX , y_text),line, font=font, fill=text_color,align="left")
            y_text += line_height
        return y_text

    def textWrap(self,string,font):
        newLine = False

        x=0
        lastSpaceIndex = 0
        lastXvalue = 0

        insertPositions = []
        
        for i in range(len(string)):
            x+=font.getsize(string[i])[0]

            if x > self.maxWidth-10:
                insertPositions.append(lastSpaceIndex)
                x=x-lastXvalue

            if string[i] == " ":
                lastSpaceIndex = i
                lastXvalue = x

            if string[i]=="\n":
                x=0

        for i in insertPositions:
            string = string[:i] + '\n' + string[i+1:]

        
        
        return string.split('\n')

#downloads yt videos
class YtHandler:
    def download(self,link,name):
        youTube = pytube.YouTube(link)
        stream = youTube.streams.get_highest_resolution()
        
        if name:
            stream.download(output_path="tempFiles",filename=name+".mp4")
        else:
            stream.download(output_path="tempFiles")
        
        bg =VideoFileClip(f"tempFiles/{name}.mp4")
        bg= bg.without_audio()
        w,h = bg.size
        #aspect ratio correction
        ratio =w/h
        if ratio > 0.5625:
            bg = bg.fx(mpe.vfx.crop, x_center=w/2 , y_center=h/2,width=h*0.5625, height=h)
        elif ratio < 0.5625:
            bg = bg.fx(mpe.vfx.crop, x_center=w/2 , y_center=h/2,width=w, height=w*0.5625)

        w,h = bg.size
        bg = bg.resize(1080/w)
        print("This may take a while, this saves time when actually making the videos by re cropping and scaling :)")
        bg.write_videofile(f"bgFootage/{name}.mp4",fps = 24)

#user interaction with the rest of the stuff
class Menu:
    def __init__(self):
        self.logo = """
        ████████╗██╗██╗  ██╗██████╗  ██████╗ ████████╗
        ╚══██╔══╝██║██║ ██╔╝██╔══██╗██╔═══██╗╚══██╔══╝
           ██║   ██║█████╔╝ ██████╔╝██║   ██║   ██║   
           ██║   ██║██╔═██╗ ██╔══██╗██║   ██║   ██║   
           ██║   ██║██║  ██╗██████╔╝╚██████╔╝   ██║   
           ╚═╝   ╚═╝╚═╝  ╚═╝╚═════╝  ╚═════╝    ╚═╝  
            """

        self.yt = YtHandler()
        self.edit = EditHandler()

        self.reddit = praw.Reddit("bot")

#as main as a menu can get, well maybe not. anyway its a main menu
    def start(self):
        os.system('cls' if os.name == 'nt' else 'clear')
        print(self.logo)
        choice = input("""Enter Choice:
    1.Video From Scratch
    2.Video From Preset
    3.Video From Post ID(s)
    4.Manage Presets
    5.Manage Background Footage
>""")
        if choice == "1":
            self.scratchVideo()
        elif choice == "2":
            print(f"{choice} chosen")
        elif choice == "3":
            self.idVideo()
        elif choice == "4":
            print(f"{choice} chosen")
        elif choice == "5":
            self.bgManage()
        else:
            self.start()
    
#background footage managment submenu
    def bgManage(self):
        os.system('cls' if os.name == 'nt' else 'clear')
        print(self.logo)
        print("Files:")
        files = os.listdir("bgFootage")
        for x in range(len(files)):
            print ("    "+str(x)+". "+files[x])
        choice = input("""\nEnter Choice:
    1.Download New Video
    2.Delete Video
    3.Go Back
>""")

        if choice == "1":
            link = input("Enter link of desired video e.g.\"https://www.youtube.com/watch?v=dQw4w9WgXcQ\"\n>")
            name = input("Enter name of file (no file extention, leave blank for default)\n>")
            self.yt.download(link,name)
        elif choice == "2":
            unLuckyNo = int(input("Enter number of file to be deleted\n>"))
            os.remove(f"bgFootage/{files[unLuckyNo]}")
        elif choice == "3":
            self.start()
        self.bgManage()



#make video from scratch with option to save settings used as preset at the end
    def scratchVideo(self):
        os.system('cls' if os.name == 'nt' else 'clear')
        print(self.logo)

        print("Files:")
        files = os.listdir("bgFootage")
        for x in range(len(files)):
            print ("    "+str(x)+". "+files[x])

        bgChoice = input("Enter number of desired background video(leave blank for random)\n>")
        if not bgChoice.isnumeric():
            bgChoice = random.randint(0,len(files)-1)
            
        sub = input("Enter subreddit name (exclude the r/), you can add multiple with a \"+\" e.g. askreddit+trueoffychest\n>")

        sort = input("Enter sorting method (hot,new,top, or rising, defaults to top)\n>")
        if sort not in ["hot","new","top","rising"]:
            sort = "top"
        if sort =="top":
            timeFilt = input("Enter time filter (hour, month, year, all, week, day), defualts to day\n>")
            if timeFilt not in ["hour","day","week","month","year","all"]:
                timeFilt = "day"
        else:
            timeFilt = "Hi person reading my code sorry for the mess it is very late, hope this thing works for u if you are using it"

        postNo = int(input("Enter number of posts in the video\n>"))
        commentNo = int(input("Enter number of comments per post\n>"))

        post = self.edit.postFromSort(self.reddit,sub,postNo,commentNo,sort,timeFilt)

        self.edit.greenScreen(post,"bgFootage/"+files[int(bgChoice)]).write_videofile("out.mp4",fps = 24)

        self.start()



#generate video from post id
    def idVideo(self):
        os.system('cls' if os.name == 'nt' else 'clear')
        print(self.logo)

        print("Files:")
        files = os.listdir("bgFootage")
        for x in range(len(files)):
            print ("    "+str(x)+". "+files[x])

        bgChoice = input("Enter number of desired background video(leave blank for random)\n>")
        if not bgChoice.isnumeric():
            bgChoice = random.randint(0,len(files)-1)

        ids = []
        print("The post id is the letter code in the url of reddit posts, for example in the url https://www.reddit.com/r/196/comments/v0cfi4/im_nuclearule/,\nthe post ID would be \"v0cfi4\".\nEnter post IDs, enter any single char when done e.g. \"Q\"")
        while(True):
            postID = input(">")
            if(len(postID)==1):
                break
            else:
                ids.append(postID)

        commentNo = int(input("Enter comment number per post\n>"))

        clip = self.edit.postFromIds(self.reddit,ids,commentNo)#.write_videofile("out.mp4")
        bg = VideoFileClip("bgFootage/"+files[int(bgChoice)])
        
        self.edit.greenScreen(clip,"bgFootage/"+files[int(bgChoice)]).write_videofile("out.mp4",fps = 24)

        self.start()

if __name__ == '__main__':
    
    u = UtilityHandler()
    u.cleanFiles()
    if not os.path.exists("praw.ini"):
        u.firstTimeSetup()
    m = Menu()
    m.start()
