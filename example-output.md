00:00:00 Cursor 1.0 just dropped. What does that
00:00:02 mean for us VI coders, AI developers,
00:00:04 chat orientated programmers, whatever
00:00:07 you want to call yourself these days. Do
00:00:08 any of the new features deserve your
00:00:10 attention? And will they inevitably help
00:00:12 you move faster in your AI and app
00:00:15 development workflows? We've got bug
00:00:17 detection, background agents, memories,
00:00:20 and rules, and one feature I think is
00:00:22 going to be my fast favorite. So, thanks
00:00:25 to tools like Cursor, Windsurf, Bolt,
00:00:27 and Lovable, you can now prototype and
00:00:30 build apps 10x faster without writing
00:00:32 any code. In my course and community,
00:00:35 I'm working with entrepreneurs and
00:00:37 entrepreneurs from Meta, Microsoft,
00:00:39 Amazon, and more, learning how to
00:00:41 upskill in AI development and launch new
00:00:43 products in record time. So, if you
00:00:45 haven't been paying attention, you might
00:00:47 have missed a subtle shift in AI
00:00:49 development workflows. We're used to
00:00:51 agents writing and editing code as pair
00:00:54 programmers synchronously, but now we're
00:00:57 increasingly seeing the idea of peer
00:01:00 programmers or asynchronous programmers
00:01:02 where we set these tasks in motion
00:01:05 either through issues or requests or
00:01:08 background agents and we go about doing
00:01:10 other things. I don't recommend this for
00:01:13 beginners. just get used to working with
00:01:14 one model at a time, but I'm starting to
00:01:17 use this workflow increasingly on my
00:01:19 more advanced projects. The caveat is
00:01:22 these agents still make plenty of
00:01:24 mistakes and I find the best way to work
00:01:26 with them is in a supervised manner when
00:01:28 you can see what's going on. But this
00:01:30 new development for cursor means you can
00:01:32 actually see and keep an eye on what's
00:01:34 happening in the virtual server. And you
00:01:36 can do the same with GitHub Copilot,
00:01:38 something I covered in a previous video.
00:01:40 Setting up background agents is actually
00:01:42 pretty easy. You go to background agents
00:01:45 here in cursor settings. You can reach
00:01:47 that up in the top right. So let's click
00:01:49 on background agents here. So not a
00:01:51 requirement, but you can set up an
00:01:53 environment file and that is a JSON file
00:01:56 which has all the instructions for
00:01:57 setting up your specific environment. So
00:01:59 when you set up your local machine, you
00:02:01 have to install node, you have to
00:02:03 install git, all those various different
00:02:05 packages. You might want to include
00:02:07 those instructions specifically here. If
00:02:09 you have a particularly unique
00:02:10 environment, you need to give the
00:02:12 background agent access to your GitHub.
00:02:14 So that means that it can clone down
00:02:16 your repository. It can create branches
00:02:18 and push and pull all the things that
00:02:20 you want to do in terms of pull requests
00:02:23 and a typical
00:02:25 workflow. So it runs a basic
00:02:28 environment. This is Iuntu. And you can
00:02:30 actually use a Docker file if you're
00:02:32 familiar with Docker to spin it up
00:02:34 exactly the way you want. But if it's
00:02:37 pretty simple, you can actually opt to
00:02:39 set up the machine interactively. So if
00:02:41 I click on this, and what I've got here
00:02:43 is a starter kit with Nex.js, Shad, CN,
00:02:47 Superbase, Prisma, Neon, etc. All set
00:02:50 up, ready to go. It's part of the
00:02:52 community if you want to join. It really
00:02:54 helps you get started quickly with your
00:02:56 projects. So essentially it's connected
00:02:58 to that GitHub. Um it's created a
00:03:01 machine snapshot. So I can then decide
00:03:04 to okay I need to install my node
00:03:06 modules. I need to run my server. Maybe
00:03:09 there's some other kind of linting
00:03:10 configuration or test setup that I want
00:03:12 to put in place if I haven't set up a
00:03:14 docker file. And then when I'm happy I
00:03:17 can basically take a snapshot. So that
00:03:19 means that our environment is going to
00:03:21 be launched at the point in time where
00:03:23 you've got everything set up. What you
00:03:25 should have then essentially is a
00:03:26 background environment that is ready to
00:03:29 run. So to get started with background
00:03:32 agents, just click this little button up
00:03:34 here, the little cloud, and it says show
00:03:35 background agents. The chat interface
00:03:37 here is just like the traditional one.
00:03:39 You type in whatever you want in terms
00:03:41 of a prompt. You can see here that you
00:03:43 can select whichever model that you want
00:03:45 to use. They all default to the max
00:03:48 setting, which is the maximum context
00:03:50 and actually the maximum cost. I think
00:03:52 that's fixed in place for now and it
00:03:54 might change in the future. So just bear
00:03:56 in mind that these background agents are
00:03:57 going to cost you a little bit more in
00:04:00 the short term. You can select what
00:04:02 branch you're using. Again, if you're
00:04:04 working with AI, I highly recommend you
00:04:06 use branching in Git so that when you're
00:04:08 creating a new feature or you're adding
00:04:10 something in, you create that branch,
00:04:12 you work on it. If something goes
00:04:13 horribly wrong or spaghetti code shows
00:04:16 up, you can revert back in time or if
00:04:19 it's successful, you can just save those
00:04:21 changes or commit them and then merge
00:04:23 them back into the main. Just a safe way
00:04:24 to work with AI, especially when you get
00:04:27 to production. You can set up an
00:04:29 environment JSON and that's pretty cool
00:04:31 because you can set up how the
00:04:33 environment should be run. Save that and
00:04:37 then other people in your team can
00:04:39 actually copy down that environment and
00:04:40 use the same one. So by environment I
00:04:43 mean when we run this background agents
00:04:46 it's not going to run on our system.
00:04:48 It's going to be run in the cloud just
00:04:50 like a code space in GitHub or VS code.
00:04:53 GitHub actually has something very
00:04:55 similar. So when we run this agent it's
00:04:57 going to run in a virtual environment in
00:05:00 the cloud. So technically we can spin up