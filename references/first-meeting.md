# First meeting  
  
Understanding and Application of Posture Analysis in Project  
This article mainly discusses the importance of posture and how to identify good and bad posture through image processing. The author first emphasizes the significance of posture, then introduces the methods and steps of the project. The project requires the identification of good and bad posture, which involves image processing technology.  
Data training and model evaluation for posture detection  
This article mainly discusses the methods and applications of training data. Firstly, the author mentioned using the yellow program and the Belo model for training, which involves using a dataset to train the model to recognize different postures and then evaluating the model's performance. In terms of app development, after training and testing the data, a camera can be used for practical testing to judge whether the posture is good or bad.  
The application of posture detection technology and improvement methods  
This article mainly discusses the importance of posture and how to detect good and bad posture. The author suggests that posture should be assessed from multiple points, such as from the shoulders to the ears, shoulders to the hips, and shoulders to the knees. By observing these angles, one can determine whether the posture is good or bad.  
Data set selection and model training for posture detection  
This text mainly discusses the importance of data sets for training models, especially in the field of posture detection. The author suggests using a data set that includes full-body images to train the model, so that it can detect good and bad posture.  
Team Learning and Project Progress Sharing  
This text mainly discusses the importance of posture detection and how to implement it using Python. First, it is necessary to set up the Python environment and learn how to run code. Then, by running the program, one can observe the posture of others to judge whether they are in a good posture. Next, it is important to conduct training and testing to improve the accuracy of posture detection.  
Team collaboration and project direction discussion  
This article mainly discusses the content and expectations of a summer program. First, the author emphasizes the importance of team collaboration and encourages everyone to actively participate and interact in the group. Secondly, the author shares some technical issues encountered during the project, such as syntax errors, and provides some solutions, such as using AI tools like ChatGPT and DeepSeek.  
Project Progress Sharing and Team Collaboration Discussion  
During this meeting, the participants discussed the project and asked how to obtain more information from the school members. The meeting also mentioned that the project will be recorded and uploaded to WeChat for everyone to try and practice on their own. The next meeting will be held on Tuesday at 11 o'clock, where everyone will share their progress, including what they have done, the courts they have handled, etc.  
  
**会议主题** ：人体姿态检测项目启动与培训 **发言人** ：Gomesh Nair、Alena、tianxu.liu、Jiapeng Xuan、Yuqi.Jiao **会议摘要** ：本次会议Gomesh Nair明确了人体姿态检测项目的技术路线与评估标准，重点强调了侧视图检测策略及数据集的构建方法，并布置了全员环境搭建与基线模型运行的周度任务。  
  
## 一、项目核心定义与检测策略  
针对“姿态（Posture）”与“姿势（Pose）”的混淆问题，会议明确了项目的核心目标及技术实现路径：  
1. 姿态检测的物理定义  
* **核心概念界定** ：项目聚焦于“姿态（Posture）”，特指人体站立时的整体体态，而非特定动作或手势（Pose）。  
* **检测维度** ：重点检测人体侧面（Sideways）视图，通过分析头部、肩部、躯干、臀部及膝盖的相对位置关系来判断姿态好坏。  
2. 技术实现逻辑  
* **关键点标注** ：需在图像中标注头部、耳朵、肩部、躯干、臀部、膝盖等关键点，构建人体骨骼线。  
* **角度计算判定** ：通过计算关键点连线之间的角度（如头部与肩部连线、肩部与臀部连线）来判断是否偏离直线。若角度大于零度（存在倾斜或弯曲），即判定为不良姿态。  
## 二、数据采集与模型训练规范  
为确保模型泛化能力，会议对数据集构建及训练流程提出了具体要求：  
1. 数据来源与处理  
* **多源数据采集** ：建议结合一手数据（Primary Source，如拍摄朋友或自己的站立照片）和二手数据（Secondary Source，如网络图片）构建数据集。  
* **数据筛选标准** ：优先选择包含完整身体（从头到脚）的侧视图图像，避免使用坐姿或遮挡严重的图片，以降低检测偏差。  
* **数据增强策略** ：鼓励使用算法生成合成数据集（Synthetic Dataset），以扩充数据量并提升模型准确性。  
2. 模型训练与评估指标  
* **技术栈选择** ：推荐使用 YOLO（You Only Look Once）模型或 OpenCV 相关库进行训练，也可使用 MediaPipe 等库进行关键点检测。  
* **评估标准** ：模型需输出 F1 Score、Mean Average Precision（mAP）等标准机器学习指标，以量化检测精度。  
## 三、项目交付物与验收标准  
会议明确了项目的最终产出形式及质量要求：  
1. 功能交付要求  
* **实时检测能力** ：系统需支持实时检测（Real-time）或视频录制检测，能够通过摄像头捕捉人体姿态并实时反馈“好/坏”结果。  
* **量化输出** ：除了定性判断，鼓励系统输出具体的角度数值（Degree of Tilt），量化不良姿态的程度。  
2. 学术与展示要求  
* **海报展示** ：最终成果将以海报（Poster）形式呈现，需包含研究问题、摘要、方法论及实验结果。  
* **环境兼容性** ：代码必须确保在中国大陆网络环境下（无需 VPN）能够正常运行，以便于最终演示。  
## 四、财务与资源支持  
1. 经费预算分配  
* **项目经费** ：学校为每位讲师（PI）提供 6000 元人民币的项目经费，用于支持材料采购或学生津贴。  
* **分配方案** ：讲师负责的两个项目将共享该笔经费，具体分配方案后续将根据实际情况确定。  
2. 资源获取渠道  
* **代码与数据集** ：讲师将提供基础的代码框架及部分数据集供学生参考和使用。  
* **学术支持** ：讲师将分享相关学术论文及参考资料，以辅助项目研究。  
## 五、QA 环节  
1. 关于检测场景的确认  
* **【提问人】Alena** ：是否需要同时检测坐姿和站姿？  
* **【回答人】Gomesh Nair** ：本项目仅需检测站姿（Standing），无需处理坐姿检测。  
2. 关于下周任务的确认  
* **【提问人】Alena** ：下周我们是否需要复现您今天演示的基础模型？  
* **【回答人】Gomesh Nair** ：是的。下周的重点是让每位成员运行我提供的代码，展示基本的骨架检测能力，以此评估团队的技术基础。  
  
## 六、待办事项  
* 将会议录屏、代码、数据集及相关文档上传至微信群。 ** @Gomesh Nair**  
* 更改会议软件昵称为英文名，以便讲师识别。 @tianxu.liu ** @Jiapeng Xuan** @Yuqi.Jiao  
* 搭建 Python 环境（推荐 PyCharm），运行讲师提供的代码框架，并实现基本的骨架检测功能。 @Alena @tianxu.liu ** @Jiapeng Xuan** @Yuqi.Jiao  
* 准备在下周二（23日）的会议上展示个人运行结果及初步进展。 @Alena @tianxu.liu ** @Jiapeng Xuan** @Yuqi.Jiao  
  
会议转写 Gomesh Nair 00:00  
Project because usually a lot of students will get confused because they confuse between posture and also post. So like this, for example, this is a post. But when you stand, that is a posture. So usually when this project I've given to a student previously.   
Gomesh Nair 00:27  
But the student understand it as a pose rather than posture, all right. So today I'll be talking to you about that. I hope you have looked at some of the materials that I've given you all. The Posture Possible website, so there is a lot of information about this particular project, so a good postureversus. Bad posture and so on, so this is the thing that you need to do so basically, yes, you will be doing some image processing. I will depend on you whether you want to do real time or maybe a video recording for the person or app, you know, so what is my understanding is so before that. Before that,   
Gomesh Nair 01:16  
let me just share my screen. To give you all some. Briefing on this. Project. Can you see my screen? Please maybe say something if you can see.   
Alena 01:40  
Yes, we can see.   
Gomesh Nair 01:43  
Ok, good so I hope the rest is the same. You can type in the chat box too if you want you know so so this is the website that I've given your. I hope you read about it about posture, so this is what I mean by posture basically when you stand from from the frontal area and from the side area.   
Gomesh Nair 02:07  
We this project is to just identify if the person is having a bad posture or his posture is good, all right. So that is the only thing about this project and yes, you will use image processing to identify that, so in order for you to do this, it is important for you to know what is a good posture and what is a best posture.   
Gomesh Nair 02:33  
So we I will expect you all to read from here. So because there is many types of posture that sometimes. Can be consider as bad, but it is actually okay, but for me I don't want to go into so complex detail on the project on the posture. I will want you to have just a normal measurement. For example, if you look at my hand, imagine this is the head. You know the one that I'm holding here is the head. So if all this is straight, so this is good posture so suddenly if you see the person is slanting a bit, you know maybe bending a bit, so you have like a straight line here to see the degree between. The posture and then your system will be identifying it as having a bad posture, you know so just that. So basically that is about the project. I have also given your some materials on the timeline. Basically this is our method, what I want you all to do now I have collected some data set. I will later after this meeting I will give you some codes that I've done myself. And also some data set that I also basically collected from some website. But that particular data set I will show you on. What are the content of the data set? All right, but in order for you to to basically complete this project is that you need to train your model.   
Gomesh Nair 04:15  
With a good and bad data service, so so, for first is you need to have some collection of data you can gather posture images from. Primary source or secondary source? The primary source here being. Maybe you want to get picture from your friend.   
Gomesh Nair 04:38  
Asking them to stand straight and then you take the picture or then you want you identify a friend that is having a bad posture that you take the picture of the friend. So these are primary data set. Basically, these are the data set that you are collecting. The secondary data set is definitely images from internet any other sources that you can get your hands to. And this particular data set, you may be preprocessing or maybe filtering the images, and then you will label your key point of the human body major. So here we want to label the. The point from the head? Maybe you want to choose the year to the shoulder, to your torso, to the hip, to the knee, you know. So when you put all this point here, you kind of get like a skeleton.   
Gomesh Nair 05:32  
And then from that skeleton you will map with a good posture and you will basically get the angle between like for example, only head and straight here. So if your head has an angle like this. So you will just basically anything that is above zero degrees from that angle is considered as a bad posture because they are slouching or they are what you call this looking down. Okay, i hope you get the point so. Remember, you can ask question if you don't understand that from here on what is just machine learning ready. You can train your data, speed your data training validation, test this.   
Gomesh Nair 06:16  
I will leave it to you all. How do you train your data? My initial methodology is using the yellow program. The model to Belo is a yeah open Cv kind of a model. You train it using your data set to detect these postures and then you can evaluate the Matrix.   
Gomesh Nair 06:39  
So this this particular data set will be good for us for maybe writing a paper and so on. But and also the post serve poster report result, right? So you can basically measure based on the data set to see which are having bad and which is having good.   
Gomesh Nair 07:00  
What is the accuracy of your model F one score? Mean average position? Those to those particular thing, which normally is a standard result. For machine learning algorithms, right, all right? And then here is where app development comes in. So what I mean by app development is that. Upon training and testing your data, you should be able to have Aa camera that can test with your friend so your friend can come in front or you yourself can. Maybe come in front of the camera and you have a skeleton there to detect if your poster is good or bad based on how you set. 啊有。Program,   
Gomesh Nair 07:48  
so for example, let me just show you one model that I have just created. So for example, later, i'll just pass you some of this model. And it run for a while.   
Gomesh Nair 08:30  
Supposed to have a video here? But I think since I am using this for this app. Kimi, said Kalen. How do I demonstrate? Using this camera you got using this in. Henson. It is not coming up.   
Gomesh Nair 09:20  
Yeah,   
Gomesh Nair 09:20  
so can you see this? This is basically what we call as a skeleton, so this this particular point here are skeleton, so for example, this is just a rough program. Maybe you can edit from that, so why it's saying good posture is because the line between each shoulders are the same. So for example, if I were to tilt up a bit and then it's saying un even shoulders,   
Gomesh Nair 09:44  
you know or the other side ok, or if I were to stand, it has my entire skeleton here, you know, so these are the points that basically you see the points red color here. These are all the points, so basically these are skeletons so it just follows it. It is already detecting, but if I go even further it can detect my leg. Yeah, i think so you know, so you supposed to have some better points here. So for example, from my front tell here it is looking like good posture, so imagine if I slide so you see uneven shoulder, you know so, but this is still not accurate. You know, still not accurate because for example, saying that this is good for shades from the front of side. Yeah, maybe maybe it's okay, but sometimes some people have slight using some slight increment here. Is still not detecting Only after you go Really detailed up to the level the camera can see. Then it will say bad posture. You and also maybe the sideways, you know, so the sideways using slouching. Ok, maybe you see here, so it's not detecting my Maybe. They still saying good posture, so then you can. Some of your maybe can improve this particular skeleton right? I will give each of you all this code so you can improve for the example. You know,   
Gomesh Nair 11:10  
seeing this and so on, so you know, i hope you get the idea. So this is something that I train using just a simple database. What you call this library so, but then what I want from you is maybe to train using some data set and if you do not have sufficient data set. You can have or do some algorithm to generate synthetic data set.   
Gomesh Nair 11:43  
That means you use existing data set to create and more data set so that. Your system will be. Accurate. Okay, so this is just the idea that I have here. Okay. So this is.   
Gomesh Nair 12:19  
All right, so this is the idea behind the Porsche. Project anyone have any questions so far.   
Alena 12:33  
Sorry, i have one question. So we need to detect like the posture when we sitting and the the person sitting and also stand like this whole body.   
Gomesh Nair 12:47  
Yes, yes,   
Gomesh Nair 12:48  
i would prefer you to take only when standing. No need sitting.   
Alena 12:52  
Mhm, so only when the person standing like front side for us.   
Gomesh Nair 12:55  
And then yeah, and I would also prefer you to take sight, because the looking at fronter sometimes is not accurate.   
Alena 13:04  
嗯哼。  
Gomesh Nair 13:06  
You know we we don't have many people having slouching shoulders like this,   
Alena 13:06  
嗯哼。  
Gomesh Nair 13:10  
which which our eyes can actually detect. All the image can actually detect. The point is not that accurate,   
Gomesh Nair 13:16  
but from side is easy to see like for for me example, you can also use me a subject. My posture is back,   
Alena 13:17  
哼哼。  
Gomesh Nair 13:23  
so you look at my head, you look at my shoulder at the back. I'm supposed to be something like this, you know, but my head is going in front so you can see there's a slight bend here, so if you have like a straight line here, you can basically get a degree of. How my head is tilt in front?   
Alena 13:23  
哼哼。  
Gomesh Nair 13:40  
Basically it just means that my coach is already bad from the front side. But talking about that, looking at the images that I give you all yesterday, let me just pull out some of the images. Like you see here So101, part bad posture is like, for example. For example. That you see here, so this is a good process. So for example, if you take the ears ears to the shoulder, to the hip to the knee, so if you if you imagine, it's kind of like a straight line from the ear up to the knee and the ankle, so this is considered as a good posture, whereas if you look at the bad posture from the shoulder to the ear, if you draw a straight line here, there is an angle between the shoulder line and the ear line here, so there is an angle here. Basically, looking at this part, it is already a bad posture in the cranium side or the head side, then looking at from the shoulder to the. Point of your hip. So this is also a bad angle already because looking at this to the hip size is supposed to be straight, but this has slant so there is a slanting part from the shoulder. To the hip and maybe to the knee. Definitely your system or your code can detect if there's one.   
Gomesh Nair 15:30  
Definitely they say it is a bad posture. But we want it to be like multiple points where it can detect the angle, where the posture is bad, you know, and and maybe you can ask your friend later on to move the head and so on so that the system can detect a correct posture so your system should be able to.   
Gomesh Nair 15:52  
Detect this in the first place and then when you ask them to sit up correctly and maybe do some some way where this is, the system will detect it to be a correct post. It's more like us. Advising, for example, a person which have a bad posture, which is a good posture, and and and and you know, maybe they can do some kind of exercise training to, you know, make the posture good, you know, but these are. The the advising part is maybe the future but for now is just to detect a good posture, a bad posture. second thing is to get the result. Like I said all these f one and maybe so on main loose for your surf report. Okay,   
Gomesh Nair 16:39  
so once once you do this, then we can you know time by time update on your current progress and so on. So this is. The the the thing about Posture. Any other question. On the rest, you all understand. Ok, yeah, so I hope you get the idea here. So basically let me see. I will give you all these materials too. So if you, if you don't really understand, you can prefer to here that for example, if yourself. 呃 yourself 呃呃。Result is finally for you to present your poster so this particular document can serve as your. Guideline like, for example, research question is already being given here. Abstract is already being given here, some methodology, part is already being given here and so on, so I will give you this information too for you to read and also to. Conduct your experiment and also data collection.   
Gomesh Nair 17:52  
And so on. All right, i will also show you some data set that I've downloaded. So for example, here. So this data set. I think I download in. I know mistake in. K. Girl lady. So there's a lot of data sets here if you want to train your model. But under like what Alena was asking, which is what I also want. I only want a data set. That is like this, you know not like this. I sorry something straight. For example, yeah you see this guy over here. It has a full view from the top until to the bottom so you can for example if you are training. 呃哒哒呃。  
Gomesh Nair 18:42  
Doing some point here you can actually point, and maybe just, you know, detect the straight line or a good posture and so on. So when you train the data on good posture or bad posture, this particular data should be able to know which is which, for example, if you see something like this. And when you test it using this particular model, first thing it should be able to tell you is the first result is definitely the result shows it's a bad posture because from the shoulder to the head it has an angle That. But how many percentage is the? And go to third, that one. You should have some measurement to like if you can do some kind of like a called to detect the angle between each of the. That posture that will be a plus point for you, and that will be something that for this particular project, you have the chance to maybe win the competition for best poster or best project,   
Gomesh Nair 19:41  
and so on and so for because. You can detect this itself. Another thing is that I give you an option here though I would want it, but I give you an option. Here is for you to do either real time. All image video recording so Ii live it to your the this team to decide if you want to do real time. Why I mean by real time is like what I did just now. It is actually detecting me and whenever I do my post you have the indication of good or bad poster, but mine is very very simple. I just take home library, it's already detected my eyes and so on and it just saved good or bad poster. It did not give you the the degree of. How much tilt or movement that I made from the sideways. It did not give me the frontal or the head part. So these are the things that I want you as a team. To do it Ok so that is the requirement here. Of course this is recorded so you can officely play back and understand what I want. So this this is some data that I collected which is even imperfect because you have something like this, you know, and. If you really want to say good posture, bad posture you see from the ear to the shoulder definitely. This is perhaps a bad posture but the hip.   
Gomesh Nair 21:03  
But this is also a seating so I will always depend on your how you want to filter your data. Or you want to train initial data using this model? You know so since some of your most of you are from the Ai and machine learning side that you should be able to do this, i believe. All right, so this is one data set. I think I have another data set here. This is human post, this one I won't give you, so this is the difference between this, but this is already annotated. You see it's already been. I can give you this if you want, but I I I will think this is will cause huge bias in your data. So maybe I don't give you this. But if you you are still requesting just to train a model or you think your model is need some more data, then you can use this, but I would prefer for you to use the actual data set. But again, like I say you see, for example, here.   
Gomesh Nair 22:05  
You have only few data that, having like the full body, feel like, for example, here you know there's only few others are all something else, you know. Maybe you might need to take collect data from your site. You can use your friends. You can use yourself to just stand in the white background for them to stand in the sideways. Just get a photo from them. Ask them to move frontal ways and get a front if you want. But for this project, i will only ask you to focus on the sideways because that is the best way for you to see posture detection and it's easier, easier from the front way. It's not really easy because. The sensitivity of the camera to detect slight angle. I don't think so is there. But or maybe it needs more processing power and so on and so forth, right? If you can do it,   
Gomesh Nair 23:04  
that will be good, but if you're not, then I'm I'm still Ok. So for me my focus is on the sideways. Sideways is very easy for you to detect angle from the point that you have already detected from your reference point. So imagine you have a reference point in the coded algorithm in the camera and then you, maybe when you have a friend to come in there and that particular point is also maybe overlapping with the point that you give and then you can should be able to find each angle.   
Gomesh Nair 23:35  
And for you to decide if it's a bad posture or good posture. All right, so that is one thing. So I mentioned to you about this information. The quote I will give it to you all. Another thing is on the.   
Gomesh Nair 24:14  
I also start some papers here which I will give it to you. Maybe you can read some of the papers that is related to posture. Remember, don't confuse between posts. You know the post peace? These are poses, you know like calling the hand. These are posts. We don't want posts, we want posture and the posture is just standing posture. I don't want sitting Ok. I want a fool from the head to the heel, the full detection of the bigger. Perhaps I think basically that is about it from my discussion here, so what I want you all to do is that each of you, all, everyone of you. Once I give you this code, everyone has to be doing this together. You know what I mean by that is that next week, when I meet with you all again, i would want each of you all to run the program yourself. And show me, what did you get, everyone of your,   
Gomesh Nair 25:25  
you know, the reason is because the previous year we have a comment that some students are given lesser load than the other student, even though we work as a team. You know, so I want each of you all. Though this is a surf project. My ultimate goal is the learning experience that you will have. The learning experience I want you to have is how to familiarize yourself with.   
Gomesh Nair 25:53  
Maybe setting up Python Interpreter Python Platform. Getting the code to run in your system, using some training and testing, you know those things, so from end to end, i want all of you all to do this. So next week, when I have a meeting, i want each of you all to show me your progress. What have you done? Additionally, as compared to what I have given you so,   
Gomesh Nair 26:22  
which which means that throughout the week before our next meeting, if you have any question, you can always text me you want to meet with me personally in. Tension meeting, just let me know, all right. So after next week, after next week, we will decide which direction we want to go based on. The capacity of the team? All right. Ok, so if the team I want to see what is the capability of the deep, so based on that, i will give you the project,   
Gomesh Nair 27:01  
what do you call this? How hard or how easy should the project be given to you? You understand that. We have any question.   
Alena 27:14  
Yes, so yes. So for the next week we need to do like to this basic model that you showed today. Yes.   
Gomesh Nair 27:23  
Yeah, i will give you the code, you can test my code and but like I said, my code is just generally based on looking at me, but the training testing part I haven't done so I will give you the data you can outsource or find any code that you can train and test the model to.   
Gomesh Nair 27:41  
Maybe next week I can see a structure of a skeleton and your data going showing that maybe you know some detection has been provided and so on next week is just for me to see your capability. In running the code, so everybody you, you, you elan,   
Gomesh Nair 28:06  
everybody will need to do this and show us your result. This result is not the final result. This result is just for me to measure the capacity of the team. How, how good are y'all? How much of time needed for you all to do things? Or what is my scope? Should I narrow it or improve it and so on? Of course, like I said, the learning experience has to be taken into consideration. I want all of you all to have a very good experience in running this kind of code.   
Gomesh Nair 28:36  
That's what summer program is about. Apart from that is that upon you giving me the impression of your capability is where we'll now focus on the direction of the project. Where should we go? Maybe some of your saying that it's very difficult to do this. So should we remove this and so on,   
Gomesh Nair 28:56  
then we can have a discussion on that. So if some of your say no, it is it can be done. That's where the team orientation can be structured from here onwards. I will tell okay who will do what and so on and so forth, but for a start, i want everybody to do this.   
Gomesh Nair 29:12  
I want everybody to have the learning experience and and and and so on, so please be interactive in our WECHAT group. If you guys are all shy, some of your are not not comfortable speaking and all that you can always ask me question personally, you know, and but my answer will always be in the group.   
Gomesh Nair 29:35  
So Ii, but I won't say okay. This person is telling that this person telling I just say, okay, these are the concern that one of the teammates is having. So my answer to this is that so that everybody we are in the same page. So that we don't confuse on our direction and so on.   
Alena 29:57  
Ok. Thank you.   
Gomesh Nair 29:59  
All right, so here we have our main code right so the code I will just give it to you. It's easy for you to run. I'm using pycharm and if you have any other Python software you can go ahead and use it. It still works on that. But of course for me my guidance was definitely I use some help. You know, it's not that I hard harder this myself. This was helped by some Ai like Chat Gpt Deep sea.   
Gomesh Nair 30:32  
You know so on because off and on I have some problem. What I will do is I will just screen screen my problem here and upload in like. Chat Gpt or Deepseek and say this is the current syntaxerror that I'm having or these other currenterrors that I'm having how to repair it,   
Gomesh Nair 30:49  
so this particular code was. Done after being repaired many times and so on. You know so and and it's working for me. Maybe for certain of you all you have like, for example, here I'm using something called a media post. So this media post is a called library that actually does that, that what you call detection of face shoulders and all that. Yeah, so you can also use media post or some other library if you want, so no restriction in the type of. Apps, software, whatever you want to use, but the most important thing it should be working and it should be working while maybe you demonstrate it. To the external person, which also means that whatever restriction it may have in China should be removed, that means it should be compatible in our environment, our the the Internet, that we have, the servers that we are performing and all that. Because we are doing it in China, all right. So please take a look at that and run it on two different servers and like, for example,   
Gomesh Nair 32:01  
if you are some of your maybe. You know, i'm not saying that you're using, but some of your if you're using Vpn, turn off the Vpn, try to run it and see if it's if it's should be running well and so on, and so for okay. All right, so I am. I'm done with my presentation. I hope you understand my expectation. What is the project about the milestone? Because this is ten weeks and we do not have much time so and that entire ten weeks is not for you to do. Project alone the entire ten weeks is up to the point that you need to have time, maybe for a last two weeks. For you to finalize, gather your result and then start writing your report or poster, you know I don't think so. Serve you have a report. It's just a poster presentation, but we still need some time for us To, you know, have the poster print the poster.   
Gomesh Nair 32:59  
And so on? Okay, in terms of what you call any material that you use to purchase, and so on. They are providing6000 Rmb per Pi, so poor lecturer, so we but I have two project, which also means that I can allocate maybe three, three for both. Project. You know for in terms of any expenses that is allocated for this now, right? If you do not have any expenses. It may be translated to Stiper. Maybe we can pay you some amount of money. If you have no expenses for this particular project,   
Gomesh Nair 33:38  
you know, but that for money, money, methods and all that, let me get more information from some of the members in the school. How do we do that?   
Gomesh Nair 33:49  
And so on. Understand. Ok, good, so do you have any questions to us regarding this project, anything that you have in mind?   
Alena 34:15  
嗯 fornow no。  
Gomesh Nair 34:17  
Ok for now. Alina has nothing. How about you?   
Yuqi.Jiao 34:25  
No, i don't have questions.   
Gomesh Nair 34:27  
We have a question, can you?   
tianxu.liu 34:31  
I don't have to.   
Gomesh Nair 34:34  
Okay, i and what's your name? Sorry because I I don't read Chinese, so if possible you, you maybe change your name in the Englishversion so that easy for me to know who is. Attending this meeting.   
Jiapeng Xuan 34:50  
Okay, i, i don't.   
Gomesh Nair 34:53  
You don't have any question, right? Okay, so so again, this is recorded once you finish this meeting. Once you end this meeting I will upload everything in WECHAT and you can start trying and doing this project on your own, the next meeting will be the same time.   
Gomesh Nair 35:16  
Is it okay for you? We have it every Tuesday this time.   
tianxu.liu 35:22  
I think is Ok.   
Gomesh Nair 35:26  
Okay, so the next meeting we will have is on the23rd 23rd at eleven o'clock, the same time. So I this this meeting, we will look at every bodies. So from here you will share what you will done, what are the courts that you have done and then you can play it, what is your current progress and so on. It's not evaluation, anything. I just want to know your capability. So show me the best capability that you have in designing this particular project and what is the update and so on. So if one of your are doing very, very well, then we can ask the rest of the team to now focus on that and maybe each of your subtroing ideas, and what are the things that we can improve and so on so far. All right, so if everyone is have no question and and everyone is okay, i will end the meeting now so we are ending it earlier. So take care bye bye. If you have any other questions, drop me a message in WECHAT. I'm always available to reply a question. If I'm late, i will reply sooner or later. 好了。Ok guys and goes. Seeyou 拜拜。  
Alena 36:35  
Ok. Goodbye.   
Gomesh Nair 36:37  
拜拜。  
Jiapeng Xuan 36:40  
See you.  
  
  
**会议待办**  
  
Gomesh Nair will provide materials to help understand posture issues and guide the formulation of research questions, methodologies, and abstracts.  
  
Use the collected data to train a model that can classify good and bad posture  
  
Students are required to run the code and show their progress during the next meeting to assess their capabilities and adjust the project scope accordingly.  
  
Gomesh Nair will provide code for students to test and train a model for posture detection.  
  
Run the code on different servers to ensure compatibility with the environment and internet in China  
  
Discuss project direction and team roles to ensure everyone is on the same page  
  
At the next meeting on the 23rd at eleven o'clock, participants will share their project progress and ideas for improvement.  
  
Gomesh Nair will upload the meeting recording to WeChat for everyone to learn the project.  
