import { useEffect, useRef, useState } from 'react';
import './LabsPage.css'
import * as Constants from '../constants/index.ts'
import DataStreamer from './DataStreamer.tsx';
import MicButton from './MicButton.tsx';
import Header from './Header.tsx';
import OptionsModal from './OptionsModal.tsx';
import Icon from './Icon.tsx';
import ConversationLog from './ConversationLog.tsx';
import { ProcessedMessage } from '../utils/WebSocketMsgProtocol.ts';
import FeedbackButton from './FeedbackButton.tsx';

//default config, if any parameter is missing
const defaultModel = Constants.models[0];
let defaultConfig: Constants.ConfigParams = {
    model: defaultModel.id,
    stt: defaultModel.stt,
    llm: defaultModel.llm,
    tts: defaultModel.tts,
    language: defaultModel.language,
};

function LabsPage() {

// refs
    // audio streaming component
    const dataStreamerRef = useRef<{
        connect: () => void // just connect to backend
        startStreaming: () => void; // start streaming audio back and forth
        stopStreaming: () => void; // stop streaming audio
        disconnect: (flag?: boolean) => void; // disconnect from backend
        sendData: (data: any) => void; // send data to backend

    }>(null);
    
    // mic button
    const micButtonRef = useRef<{
        disable: () => void; // disable button permanently
    }>(null);

    // state
    const [scrollY, setScrollY] = useState(0);
    const [isOptionsOpen, setOptionsOpen] = useState(false);
    const [initialConfig, setInitialConfig] = useState<Constants.ConfigParams>(defaultConfig);
    const [configReady, setConfigReady] = useState(false); // track when init config ready to send to backend
    const [messages, setMessages] = useState<ProcessedMessage[]>([]); // conversation log received from backend
    const [isConversationStarted, setIsConversationStarted] = useState(false); // track if conversation has started to start revealing the conversationLog
    const [isMicSticky, setIsMicSticky] = useState(false); // Track if mic button is sticky

    // Track scroll position
    useEffect(() => {
        const handleScroll = () => {
        const scrollPosition = window.scrollY;
        setScrollY(scrollPosition);
        // Check if scrolled past the banner (75vh)
        const bannerHeight = window.innerHeight * 0.75;
        setIsMicSticky(scrollPosition > bannerHeight);
        };
        window.addEventListener('scroll', handleScroll, { passive: true });
        return () => window.removeEventListener('scroll', handleScroll);
    }, []);

    // Parse url query parameters on mount
    useEffect(() => {
        const params = new URLSearchParams(window.location.search);
        const modelId = Number(params.get('model'));
        const sttId = Number(params.get('stt'));
        const llmId = Number(params.get('llm'));
        const ttsId = Number(params.get('tts'));
        const languageId = Number(params.get('language'));

        // if all parameters present, update config
        if (params.toString() != "" &&
            modelId >= 0 && modelId < Constants.paramsNames.model.length
            && sttId >= 0 && sttId < Constants.paramsNames.stt.length
            && llmId >= 0 && llmId < Constants.paramsNames.llm.length
            && ttsId >= 0 && ttsId < Constants.paramsNames.tts.length
            && languageId >= 0 && languageId < Constants.paramsNames.language.length
        ) {

            const config = {
                model: modelId,
                stt: sttId,
                llm: llmId,
                tts: ttsId,
                language: languageId
            };
            
            console.log("Parsed config from URL:", config);
            setInitialConfig(config);
            
        } else {
            console.log("Invalid parameters in URL, using default config");
        }

        setConfigReady(true);
    }, []);

// connect to backend on mount
    useEffect(() => {
        // on page load
        if (dataStreamerRef.current) {
            dataStreamerRef.current.connect();
            console.log("Connected to backend");
        }

        // on unload
        return () => {
            if (dataStreamerRef.current) {
                dataStreamerRef.current.disconnect();
                console.log("Disconnected from backend");
            }
        }
    }, []);

// mic related
    const handleMicToggleOn = () => {
        if (dataStreamerRef.current) {
            dataStreamerRef.current.startStreaming();
            setIsConversationStarted(true); // start conversation, if not already started
            console.log("Mic toggled on");
        }
    }

    const handleMicToggleOff = () => {
        if (dataStreamerRef.current) {
            dataStreamerRef.current.stopStreaming();
            console.log("Mic toggled off");
        }
    }

    const handleEndConversation = () => {
        if (dataStreamerRef.current) {
          dataStreamerRef.current.disconnect(true); // passive disconnect
        }
        if (micButtonRef.current) {
          micButtonRef.current.disable(); // permanently disable the button
        }
        console.log("Conversation ended, mic button disabled");
      };
    
    // handle text data received from backend
    const handleDataReceived = (data: ProcessedMessage) => {
        // Attach timestamp if not present
        const msgWithTimestamp = {
            ...data,
            timestamp: (data as any).timestamp ?? Date.now(),
        };
        setMessages((prev) => [...prev, msgWithTimestamp]);
        console.log('Received message:', msgWithTimestamp);
    };


    // options modal related
    const handleToggleOptions = () => {
        setOptionsOpen((prev) => !prev);
    }

    
    // Calculate when to change header styles
    const isHeaderAtTop = scrollY > (document.querySelector('.labspage_banner_section')?.clientHeight || 0);
    
    const optionsModalButton = (
        <Icon 
            onClick={handleToggleOptions}
            altName="Settings"
            icon={Constants.icons.settings}
            size={1.8}
            backgroundColor="transparent"
            className={isHeaderAtTop ? 'icon_logo scrolled' : 'icon_logo'}
        />
    );

    return(
        <>
            <Header rightContent={optionsModalButton} isHeaderAtTop={isHeaderAtTop}/>
            <div className='labspage_container'>
                <div className='labspage_banner_section'>
                    <img src={Constants.images.banner}  alt="Voice Future LABS banner" />
                    <div className='labspage_banner_text'>
                        <div className='labspage_banner_title'>
                            <span>Voice Future</span>
                            <span>LABS</span>
                        </div>
                        <div className='labspage_banner_subtitle'>
                            <span>Experience the future of customer support
                                <br></br> while we find its voice 
                                <br></br> Once you've finished, please fill the form 
                                <br></br> using the button bottom left of the page.
                            </span>
                        </div>
                    </div>
                </div>
                <MicButton 
                    ref={micButtonRef}
                    className={`button_div ${isMicSticky ? 'sticky' : ''}`}
                    src_img={Constants.icons.microphone} 
                    onToggleOn={handleMicToggleOn}
                    onToggleOff={handleMicToggleOff}
                    />
                {isOptionsOpen && <OptionsModal onClose={handleToggleOptions} startConfigs={initialConfig}/>}
                {configReady && (
                    <DataStreamer 
                        signalEndConversation={handleEndConversation}
                        onData={handleDataReceived}
                        config={initialConfig}
                        ref={dataStreamerRef}
                    />
                )}
                <div className='labspage_bottom_section'>
                    {!isConversationStarted && 
                    <span className="labspage_bottom_text">
                        Press the button to begin
                    </span>
                    }
                </div>
                {isConversationStarted && <ConversationLog messages={messages} />}
                <FeedbackButton />
            </div>
        </>
    )
}

export default LabsPage;