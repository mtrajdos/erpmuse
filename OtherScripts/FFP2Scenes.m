function FFP2Scenes(int_SubNumber,int_Block)

% Usage EmoSportsScenes(int_SubNumber,int_Block)
%
% int_SubNumber:    number of subject 
% 
% int_Block:        number of block         
%
%
%This program presents visual stimuli via psychtoolbox
%and sends out triggers for, e.g., MEG-measurement. 

% NOTE: OSX is case sensitive!!!

%%%%%%%%%%%%%%%%%%%%%%%%%
% preliminar7
%%%%%%%%%%%%%%%%%%%%%%%%%

% nargin: number of arguments in (a function)

if nargin < 2
    disp('#####################################################');
    disp('#  This program requires two arguments, see below:  #');
    disp('#####################################################');
    help EmoSportsScenes;
    return;
elseif nargin == 2
    int_DurationPic = 0.6;%picture duration
end
clc;

% define IBB settings
% ibbSettings = ibb_define_settings;

%specified key for aborting the experiment
KbName('UnifyKeyNames');
escapeKey = KbName('Escape');

computerName = getenv('COMPUTERNAME');
if contains(computerName,'MEGSTIM')
    sendTriggers = 1;
    string_ParadigmDir = [fileparts(which('FFP2Scenes')),filesep];
else
    sendTriggers = 0;
    string_ParadigmDir = [fileparts(which('FFP2Scenes')),filesep];
end

s = RandStream.create('mt19937ar','seed',sum(100*clock));
cd (string_ParadigmDir);

% Initialize Triggers
if sendTriggers
    dio = ibb_initializeLPT_x64; % Initialize DualPortCommunication to send triggers to the CTF computer
    triggerDurationMs = 34;
    LPTtriggerDelay = 0;
end

%% Defaults for 3 blocks x 4 categories of stimuli x 25 different stimuli per group x 3 presentations each block (+ one Pre-Baseline-Block with only 2 presentations of each stimulus=100 trials) 
%(= block 1-3 = 300 stimuli respectively) 
% 25 stimuli per group is the best available at the time of writing this
% script matching the physical picture parameters, such as resolution and
% quality, color balance and brightness, size and aspect ratio, as well as
% contrast, sharpness and visibility of the contents in the image itself
% 50 pictures typically achieves good signal to noise ratio

%loads the vector consisting of numbers 1 - 4 for each condition (the vecttor*.txt-file can be created with function createvec.m and has to be converted into txt-file format via ibb_cell2file.m)
if int_Block == 0
%     vectorfilepath=strcat(string_ParadigmDir,'veclength300.txt');
%     [vectorfile]=importdata(vectorfilepath);
%     RandVec=vectorfile(1,:);
%     Deletevector=vectorfile(2:end,:);
%     dlmwrite(vectorfilepath,Deletevector,'delimiter','\t');
    RandVec = ibb_determine_StimVector([string_ParadigmDir filesep 'veclength300.txt']);
elseif int_Block == 1
%     vectorfilepath=strcat(string_ParadigmDir,'veclength300.txt');
%     [vectorfile]=importdata(vectorfilepath);
%     RandVec=vectorfile(1,:);
%     Deletevector=vectorfile(2:end,:);
%     dlmwrite(vectorfilepath,Deletevector,'delimiter','\t');
    RandVec = ibb_determine_StimVector([string_ParadigmDir filesep 'veclength300.txt']);
elseif int_Block == 2
%     vectorfilepath=strcat(string_ParadigmDir,'veclength300.txt');
%     [vectorfile]=importdata(vectorfilepath);
%     RandVec=vectorfile(1,:);
%     Deletevector=vectorfile(2:end,:);
%     dlmwrite(vectorfilepath,Deletevector,'delimiter','\t');
    RandVec = ibb_determine_StimVector([string_ParadigmDir filesep 'veclength300.txt']);
elseif int_Block == 3
%     vectorfilepath=strcat(string_ParadigmDir,'veclength300.txt');
%     [vectorfile]=importdata(vectorfilepath);
%     RandVec=vectorfile(1,:);
%     Deletevector=vectorfile(2:end,:);
%     dlmwrite(vectorfilepath,Deletevector,'delimiter','\t');
    RandVec = ibb_determine_StimVector([string_ParadigmDir filesep 'veclength300.txt']);
end

%%%%%%%%%%%%%%%%%%%%%%
% file handling
%%%%%%%%%%%%%%%%%%%%%%

% files are loaded into PTB beforehand to reduce delay due to reading
% processes

highneg_folder =strcat(string_ParadigmDir,'StimuliRenamedToPreventAccidentalUseInFFP2Youth\highneg');
filepattern = fullfile(highneg_folder,'*.jpg');
highneg = dir(filepattern);
highneg_cell = cell(1,numel(highneg));
for i = 1:numel(highneg)
  baseFileName = highneg(i).name;
  fullFileName = fullfile(highneg_folder, baseFileName);
  highneg_cell{1,i} = imread(fullFileName);
  highneg_cell{2,i} = baseFileName;
end

lowneg_folder = strcat(string_ParadigmDir,'StimuliRenamedToPreventAccidentalUseInFFP2Youth\lowneg');
filepattern = fullfile(lowneg_folder,'*.jpg');
lowneg = dir(filepattern);
lowneg_cell = cell(1,numel(lowneg));
for i = 1:numel(lowneg)
  baseFileName = lowneg(i).name;
  fullFileName = fullfile(lowneg_folder, baseFileName);
  lowneg_cell{1,i} = imread(fullFileName);
  lowneg_cell{2,i} = baseFileName;
end

highpos_folder = strcat(string_ParadigmDir,'StimuliRenamedToPreventAccidentalUseInFFP2Youth\highpos');
filepattern = fullfile(highpos_folder,'*.jpg');
highpos = dir(filepattern);
highpos_cell = cell(1,numel(highpos));
for i = 1:numel(highpos)
  baseFileName = highpos(i).name;
  fullFileName = fullfile(highpos_folder, baseFileName);
  highpos_cell{1,i} = imread(fullFileName);
  highpos_cell{2,i} = baseFileName;
end

lowpos_folder = strcat(string_ParadigmDir,'StimuliRenamedToPreventAccidentalUseInFFP2Youth\lowpos');
filepattern = fullfile(lowpos_folder,'*.jpg');
lowpos = dir(filepattern);
lowpos_cell = cell(1,numel(lowpos));
for i = 1:numel(lowpos)
  baseFileName = lowpos(i).name;
  fullFileName = fullfile(lowpos_folder, baseFileName);
  lowpos_cell{1,i} = imread(fullFileName);
  lowpos_cell{2,i} = baseFileName;
end

% shuffling cell arrays of every condition
% randperm generates a random permutation of integers
highneg_cell=highneg_cell(:,randperm(size(highneg_cell,2))); % size(nameofcellarray,numberofdimension->1=row,2=column,3=matrix)
highpos_cell=highpos_cell(:,randperm(size(highpos_cell,2)));
lowneg_cell=lowneg_cell(:,randperm(size(lowneg_cell,2)));
lowpos_cell=lowpos_cell(:,randperm(size(lowpos_cell,2)));


% Parameters
FixSize = 3;
% Parameter for the fixationdot - visual stimulus to indicate a consisten location where participant's focus is directed
% Stabilizes gaze before and during presentation

if int_Block == 0
    ntrials = (numel(highpos)+numel(lowpos)+numel(highneg)+numel(lowneg)); % number of stimuli x count for each stimulus 
elseif int_Block == 1
    ntrials = (numel(highpos)+numel(lowpos)+numel(highneg)+numel(lowneg))*3;
elseif int_Block == 2
    ntrials = (numel(highpos)+numel(lowpos)+numel(highneg)+numel(lowneg))*3;
elseif int_Block == 3
    ntrials = (numel(highpos)+numel(lowpos)+numel(highneg)+numel(lowneg))*3;
end

% Log the experiment into a .txt file under LogScenes\
% Log contains filenames of displayed scenes, subject no etc.
% Filename follows the FFP-<subjno>.txt format
string_LogDir = strcat(string_ParadigmDir,'LogScenes\');
if int_Block == 0
    string_DATfilename = strcat(string_LogDir,'FFP-',num2str(int_SubNumber),'-0.txt'); % name of data file to write to
elseif int_Block == 1
    string_DATfilename = strcat(string_LogDir,'FFP-',num2str(int_SubNumber),'-1.txt'); 
elseif int_Block == 2
    string_DATfilename = strcat(string_LogDir,'FFP-',num2str(int_SubNumber),'-2.txt'); 
elseif int_Block == 3
    string_DATfilename = strcat(string_LogDir,'FFP-',num2str(int_SubNumber),'-3.txt'); 
end
if exist(string_DATfilename, 'file')
     string_DATfilename=[ string_DATfilename,'.' datestr(now,'yyyymmdd_HH_MM_SS')];
end
% check for existing file (except for subject numbers > 99)
% Check to not overwrite data files for subject number that already exists,
% unless it is subject 99 (test subject)
if int_SubNumber<99 && fopen(string_DATfilename, 'rt')~=-1
    fclose all;
    error('data files exist!');
else
    datafilepointer = fopen(string_DATfilename,'wt'); % open ASCII file for writing
end

%% %%%%%%%%%%%%%%%%%%%%
% experiment
%%%%%%%%%%%%%%%%%%%%%%

    % check for opengl compatability
    AssertOpenGL;
    
    % get screen
    % screenNumber=ibbSettings.screenID;
    screenNumber=1;
    
    HideCursor;
    
    % Open a double buffered fullscreen window and draw a gray background
    % to front and back buffers:
    % Screen('Preference', 'SkipSyncTests', 1);

    Screen('Preference', 'SkipSyncTests', 0);
    Screen('Preference', 'SyncTestSettings', 0.001, [], [], []);
    
    Screen('Preference', 'VisualDebugLevel', 0);

    [w, wRect]=Screen('OpenWindow',screenNumber, 0,[],32,2); %[windowPtr,rect]=Screen('OpenWindow',windowPtrOrScreenNumber [,color] [,rect][,pixelSize][,numberOfBuffers])
    
    %for debugging use 
    %[w, wRect]=Screen('OpenWindow',screenNumber, 0,[0 0 800 600],32,2);
    
    hz=Screen('NominalFrameRate', w ,[],[]);
    
    % if hz ~= 120.0 %this loop is used for the presentation in the MEG chamber due to synchrony problems during a dual-screen presentation (it may be problematic, if two different frame rates are used in a dual-screen setup)
    %     Screen('CloseAll');
    %     ShowCursor;
    %     fclose(datafilepointer);
    %     fclose('all');
    %     Priority(0);
    %     clc
    %     disp('#######################################');
    %     disp('#  Please switch to 60 Hz frame rate  #');
    %     disp('#######################################');
    %     return
    % end
    
    % Parameters for the fixationdot
    hCenter = wRect(3)/2;
    vCenter = wRect(4)/2;
    
    % returns as default the mean gray value of screen
    gray=GrayIndex(screenNumber);
    
    Screen('FillRect',w, gray);
    Screen('Flip', w);
    
   
    % set priority - also set after Screen init
    % setting up max priority to minimize interference from other system
    % processes during real-time tasks
    priorityLevel=MaxPriority(w);
    Priority(priorityLevel);

    % TODO - edit instruction JPGs so they are relevant for the tablet +
    % Muse setup, including English translations
    
    if int_Block == 0
        instrname=strcat(string_ParadigmDir,'instruktion_prebaseline1.jpg');
    else
        instrname=strcat(string_ParadigmDir,'instruktion1.jpg');
    end
    
	iminstr=imread((instrname));
    % make texture
    % texture is an efficient PTB tool for quickly rendering images onto
    % the screen, allowing for control of how and when the image appears
    texinstr=Screen('MakeTexture', w, iminstr);
    tRect=Screen('Rect', texinstr);
    
    Screen('DrawTexture', w, texinstr, [], CenterRect(tRect,wRect));% draw checkerboard to the buffer//CenterRect centers the first rect into the second
    
    Screen('Flip', w); % show text/whatever is in the back buffer onto the display layer
    FlushEvents
    RestrictKeysForKbCheck(13);
    KbWait;
    
    if int_Block == 0
        instrname=strcat(string_ParadigmDir,'instruktion_prebaseline2.jpg');
    else
        instrname=strcat(string_ParadigmDir,'instruktion2.jpg');
    end
	
    iminstr=imread((instrname));
    % make texture
    texinstr=Screen('MakeTexture', w, iminstr);
    tRect=Screen('Rect', texinstr);
    
    Screen('DrawTexture', w, texinstr, [], CenterRect(tRect,wRect));% 
    
    Screen('Flip', w); % show text
    WaitSecs(1)
    KbWait;
    FlushEvents % removes residual events (key presses or mouse clicks) to avoid unintended interactions
    RestrictKeysForKbCheck([]);


    % wait a bit before starting trial
    WaitSecs(.001);
    
    % display a centered red circle
    % This works as a fixation point for reliably anchoring participant's
    % gaze, noted that this fixation point should not be "stared at"
    % too much to avoid perception of image content around it
    % Does not really matter whether it is a cross or a dot
    Screen('FillOval', w, [238 59 59], [hCenter-FixSize,vCenter-FixSize,hCenter+FixSize,vCenter+FixSize]);
     
    
    %show gray background
    [~,startrt]=Screen('Flip', w);
    while (GetSecs-startrt) <= int_DurationPic, WaitSecs(0.001);end

 
    % 1, not 0 for counters as MATLAB uses 1-based indexing
    % first array member is 1, not 0
    highneg_counter = 1;
    highpos_counter = 1;
    lowneg_counter = 1;
    lowpos_counter = 1;
     
    
    %filedescription
    if int_Block == 0
        % Pre-baseline: presenting pictures once to reduce unfamiliarity
        % effect, data is not stored for this one
        fprintf(datafilepointer, '%s\n\n', 'Pre-Baseline');
    elseif int_Block == 1
        % Baseline, presentation of images without stimulation
        fprintf(datafilepointer, '%s\n\n', 'Baseline');
    elseif int_Block == 2
        % TCDS - transcranial direct stimulation
        % The script originally copied from that study, hence its presence
        fprintf(datafilepointer, '%s\n\n', 'TDCS_I');
    elseif int_Block == 3
        fprintf(datafilepointer, '%s\n\n', 'TDCS_II');
    end
    fprintf(datafilepointer,'%s\t %s\t %s\t %s\t\t %s\t %s\t %s\n', 'Sub_Nr', 'Block', 'Trial', 'ITI', 'Pic_Duration', 'Cond', 'Stimfilename');
    
    % StartACQTrigger
    if sendTriggers
        ibb_sendLPTTrigger_x64(dio,128,triggerDurationMs/1000);
        WaitSecs(1);
    end
	
%-----------------------------------------------------------------------------------------------------------------------------------------------------%  
%%    loop through trials

    for trial=1:ntrials
        
        % shuffle arrays with every new repetition        
        if trial == 101||trial == 201;highneg_cell=highneg_cell(:,randperm(size(highneg_cell,2)));end
        if trial == 101||trial == 201;highpos_cell=highpos_cell(:,randperm(size(highpos_cell,2)));end
        if trial == 101||trial == 201;lowneg_cell=lowneg_cell(:,randperm(size(lowneg_cell,2)));end
        if trial == 101||trial == 201;lowpos_cell=lowpos_cell(:,randperm(size(lowpos_cell,2)));end
        
        % Reset counters - no more than 25 different scenes per condition
        if highneg_counter == 26; highneg_counter = 1; end
        if highpos_counter == 26; highpos_counter = 1; end
        if lowneg_counter == 26; lowneg_counter = 1; end
        if lowpos_counter == 26; lowpos_counter = 1; end
        
        %show gray screen
        slack = Screen('GetFlipInterval', w)/2; %slack is used to render your scripts timing more precisely (for more information see ECVP2007-Kleiner-slides*.pdf)
        Screen('FillOval', w, [238 59 59], [hCenter-FixSize,vCenter-FixSize,hCenter+FixSize,vCenter+FixSize]);
        fixationdot_onset=Screen('Flip', w);
        durationITI=rand(1,1)+1;
       
        %while (GetSecs-startrt) <= durationITI, WaitSecs(0.001);end
      
        % read stimulus
        if RandVec(trial) == 1 % high arousal & negative
            theTriggerValue = 55; 
            imdata = highneg_cell{1,highneg_counter};
            stimfilename = highneg_cell{2,highneg_counter};
            highneg_counter = highneg_counter + 1;
        elseif RandVec(trial) == 2 % high arousal & positive
            theTriggerValue = 66; 
            imdata = highpos_cell{1,highpos_counter};
            stimfilename = highpos_cell{2,highpos_counter};
            highpos_counter = highpos_counter + 1;
        elseif RandVec(trial) == 3 % low arousal & negative
            theTriggerValue = 77; 
            imdata = lowneg_cell{1,lowneg_counter};
            stimfilename = lowneg_cell{2,lowneg_counter};
            lowneg_counter = lowneg_counter + 1;
        elseif RandVec(trial) == 4 % low arousal & positive
            theTriggerValue = 88;  
            imdata = lowpos_cell{1,lowpos_counter};
            stimfilename = lowpos_cell{2,lowpos_counter};
            lowpos_counter = lowpos_counter + 1;
        end
    
        % make texture
        tex=Screen('MakeTexture', w, imdata);
        tRect=Screen('Rect', tex);
             
        % draw texture to backbuffer     
        Screen('DrawTexture', w, tex, [], CenterRect(tRect, wRect));
        Screen('FillOval', w, [238 59 59], [hCenter-FixSize,vCenter-FixSize,hCenter+FixSize,vCenter+FixSize])
        
        % Show stimulus on screen & record onset time
        trial_onset=Screen('Flip', w, fixationdot_onset + durationITI - slack);%flip after ITI-slack   
        if sendTriggers
%             putvalue(dio,theTriggerValue); %<<<<<<<<<<<<<< Target Trigger
%             WaitSecs(triggerDurationMs/1000);
%             putvalue(dio,0);
%             startrt-(triggerDurationMs/1000);
            ibb_sendLPTTrigger_x64(dio, theTriggerValue, triggerDurationMs/1000, LPTtriggerDelay);

        end
        Screen('Flip', w, trial_onset + int_DurationPic - slack); %trial offset (flip after picture_duration(usually 600ms))
        
        %print to file
        fprintf(datafilepointer,'%i\t %i\t %i\t %8g\t\t %g\t %g\t %s\n', ...
            int_SubNumber, ...
            int_Block, ...
            trial, ...
            durationITI,...
            int_DurationPic,...
            RandVec(trial),...
            stimfilename);
        
         
        [keyIsDown, ~, keyCode] = KbCheck; %checking for any pressed keys
        
        if keyIsDown %aborts experiment when the escape button is pressed (it has to be pressed for up to 1-2 seconds because the button press check is only at this point of the loop)
            if keyCode(escapeKey)
                fclose(datafilepointer);
                edit(string_DATfilename);
                ShowCursor;
                sca
            end
        end
               
    Screen('Close');%after presentation, the flipped image has to be closed. other way it will still feast on your memory
    
    end  % end for loop
        
%%    
    %load 'please wait' message
    if int_Block == 0     
        instrname=strcat(string_ParadigmDir,'instruktion_prebaseline3.jpg');
    else
        instrname=strcat(string_ParadigmDir,'instruktion3.jpg');
    end
    
    iminstr=imread((instrname));
    % make texture
    texinstr=Screen('MakeTexture', w, iminstr);
    tRect=Screen('Rect', texinstr);
    
    Screen('DrawTexture', w, texinstr, [], CenterRect(tRect,wRect));
    
    Screen('Flip', w); % show text
    RestrictKeysForKbCheck(13);
    KbWait;
    RestrictKeysForKbCheck([]);
    Screen('Flip', w); 
    
%%  
    % cleanup at end of experiment
    Screen('CloseAll');
    ShowCursor;
    fclose(datafilepointer);
    fclose('all');
    Priority(0);
    edit(string_DATfilename)
% catch ME1 
%     Screen('CloseAll');
%     ShowCursor;
%     fclose('all');
%     Priority(0);
%     ME1
end