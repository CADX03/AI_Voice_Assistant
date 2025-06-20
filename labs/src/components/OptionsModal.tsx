import './OptionsModal.css'
import * as Constants from '../constants/index.ts'
import Icon from './Icon.tsx';
import Dropdown from './common/Dropdown.tsx';
import { useEffect, useRef, useState } from 'react';

interface OptionsProps {
    onClose: () => void;
    startConfigs: Constants.ConfigParams;
}

const OptionsModal: React.FC<OptionsProps> = ({onClose, startConfigs}) => {

    const onHover = (entering: boolean) => {
        //todo
        // console.log("hovering", entering);
    }
    
    // update model (refers to the first model dropdown)
    const setOptionsModel = (modelIndex: number) => {
        const model = Constants.models[modelIndex];
        setSelections({
            model: modelIndex,
            stt: model.stt,
            llm: model.llm,
            tts: model.tts,
            language: model.language,
        })
    };
    
    // when the user tries differnt model, page reloads with params for that model
    const onTryModel = () => {
        console.log("try model");
        const params = new URLSearchParams({
            model: selections.model.toString(),
            stt: selections.stt.toString(),
            llm: selections.llm.toString(),
            tts: selections.tts.toString(),
            language: selections.language.toString(),
          });
        const newUrl = `${window.location.pathname}?${params.toString()}`;
        window.location.assign(newUrl);
    }
    
    //state
    const [selections, setSelections] = useState<Constants.ConfigParams>(() => {
        return startConfigs
    });
    const [showScrollHint, setShowScrollHint] = useState(false);
    const contentRef = useRef<HTMLDivElement>(null);

    useEffect(() => {
        const el = contentRef.current;
        if (!el) return;
    
        const handleScroll = () => {
            const gradientHeight = 6 * 16; // 6rem in pixels (assuming 1rem = 16px)
            const nearBottom = el.scrollHeight - el.scrollTop <= el.clientHeight + gradientHeight;
            setShowScrollHint(!nearBottom && el.scrollHeight > el.clientHeight);
        };
    
        // Initial check
        handleScroll();
    
        // Attach scroll listener
        el.addEventListener('scroll', handleScroll);
    
        return () => el.removeEventListener('scroll', handleScroll);
    }, [selections]);
    
    //update specific model parts (refers to the custom model)
    const setOptionsSTT = (index: number) => setSelections(prev => ({ ...prev, stt: index }));
    const setOptionsLLM = (index: number) => setSelections(prev => ({ ...prev, llm: index }));
    const setOptionsTTS = (index: number) => setSelections(prev => ({ ...prev, tts: index }));
    const setOptionsLanguage = (index: number) => setSelections(prev => ({ ...prev, language: index }));
    
    // decide if options are for custom model or not
    const isSelectedModelCustom = () =>
        Constants.models[selections.model].name.toLowerCase() === "custom";

    //decide if the options are showing the same model as the initial one
    const isSelectedModelSameAsInitial = () => {
        return (
            // selections.model === startConfigs.model &&
            selections.stt === startConfigs.stt &&
            selections.llm === startConfigs.llm &&
            selections.tts === startConfigs.tts &&
            selections.language === startConfigs.language
        )
    };

    return(
        <div className="modal_overlay" onClick={onClose}>
            <div 
                className="modal_content"
                onClick={(e) => e.stopPropagation()} // prevent closing when clicking inside modal
                ref={contentRef}
            > 
                <div className="modal_header">
                    <div/>
                    <span>Options</span>
                    <Icon
                        className="modal_close_icon"
                        onClick={onClose}
                        altName="Close"
                        icon={Constants.icons.cross}
                        size={1.2}
                    />
                </div>
                <div className="modal_body">
                    <div className="modal_section">
                        <div className="section_title">
                            <span className="section_title_text">Model</span>
                            {/* <Icon 
                                altName="Help"
                                icon={Constants.icons.help}
                                size={1.2}
                                onEnterHover={() => onHover(true)}
                                onLeaveHover={() => onHover(false)}
                            /> */}
                        </div>
                        <Dropdown 
                            options={Constants.paramsNames.model}
                            optionsIcons={Constants.paramsIcons.model}
                            gradient={true}
                            selectedConfigs={selections.model}
                            onChange={setOptionsModel}
                        />
                        <div className="section_body model_description">
                            <span className="section_body_text">{Constants.models[selections.model].description}</span>
                        </div>
                        {!isSelectedModelSameAsInitial() &&
                            <div className="modal_try">
                                <div className="try_button" onClick={onTryModel}>
                                    <span>TRY MODEL</span>
                                    <Icon 
                                        altName="Go-to arrow" 
                                        icon={Constants.icons.dropdown_arrow_white} 
                                        size={1.1} />
                                </div>
                            </div>
                        }
                    </div>
                    <div className="modal_section">
                        <div className="section_title">
                            <span className="section_title_text ">Components</span>
                            {/* <Icon 
                                altName="Help"
                                icon={Constants.icons.help}
                                size={1.2}
                                onEnterHover={() => onHover(true)}
                                onLeaveHover={() => onHover(false)}
                            /> */}
                        </div>
                        <div className="section_body">
                            <div className="section_component">
                                <span className={`section_subdiv_text ${isSelectedModelCustom() ? '' : 'display_subdiv_text'}`}>Speech-to-Text model</span>
                                <Dropdown 
                                    options={Constants.paramsNames.stt}
                                    optionsIcons={Constants.paramsIcons.stt}
                                    isClickable={isSelectedModelCustom()}
                                    selectedConfigs={selections.stt}
                                    onChange={setOptionsSTT}
                                />
                            </div>
                            <div className="section_component">
                                <span className={`section_subdiv_text ${isSelectedModelCustom() ? '' : 'display_subdiv_text'}`}>LLM model</span>
                                <Dropdown 
                                    options={Constants.paramsNames.llm}
                                    optionsIcons={Constants.paramsIcons.llm}
                                    isClickable={isSelectedModelCustom()}
                                    selectedConfigs={selections.llm}
                                    onChange={setOptionsLLM}
                                />
                            </div>
                            <div className="section_component">
                                <span className={`section_subdiv_text ${isSelectedModelCustom() ? '' : 'display_subdiv_text'}`}>Text-to-speech model</span>
                                <Dropdown 
                                    options={Constants.paramsNames.tts}
                                    optionsIcons={Constants.paramsIcons.tts}
                                    isClickable={isSelectedModelCustom()}
                                    selectedConfigs={selections.tts}
                                    onChange={setOptionsTTS}
                                />
                            </div>
                            <div className="section_component">
                                <span className={`section_subdiv_text ${isSelectedModelCustom() ? '' : 'display_subdiv_text'}`}>Language</span>
                                <Dropdown 
                                    options={Constants.paramsNames.language}
                                    optionsIcons={Constants.paramsIcons.language}
                                    isClickable={isSelectedModelCustom()}
                                    selectedConfigs={selections.language}
                                    onChange={setOptionsLanguage}
                                />
                            </div>
                        </div>
                    </div>
                </div>
                {showScrollHint && (
                    <div className="scroll_gradient_footer" /> // show a white gradient at the bottom, to indicate that there is more content
                )}
            </div>
        </div>
    );
}

export default OptionsModal