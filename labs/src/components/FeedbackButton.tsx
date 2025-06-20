import { useEffect, useState } from 'react';
import './FeedbackButton.css';
import Icon from './Icon.tsx';
import * as Constants from '../constants/index.ts';

function FeedbackButton() {
    const [formsLink, setFormsLink] = useState(
        "https://docs.google.com/forms/d/e/1FAIpQLSePVGPXnMtGjqAL8d1pF1b6fq416BhPSxWOraa_UdyfSW1q5w/viewform"
    );

    useEffect(() => {
        const params = new URLSearchParams(window.location.search);
        const sttId = Number(params.get('stt'));
        const llmId = Number(params.get('llm'));
        const ttsId = Number(params.get('tts'));

        const sttLabel = [
            'Google+Speech-to-text',
            'Amazon+Transcribe',
            'ElevenLabs+Speech-to-text',
            'Azure+Speech-to-text',
            'Faster+Whisper+(tiny-pt-default)',
            'Faster+Whisper+(small-pt-MyNorthAI)',
        ][sttId] || 'Google+Speech-to-text';

        const llmLabel = [
            'Gemini+(2.0+Flash)',
            'ChatGPT+4.0',
        ][llmId] || 'Gemini+(2.0+Flash)';

        const ttsLabel = [
            'Google+Text-to-speech',
            'Amazon+Polly',
            'ElevenLabs+Text-to-speech',
            'Azure+Speech+SDK',
            'Piper+TTS+(pt_PT-tug%C3%A3o-medium)',
            'Microsoft+Edge+TTS',
        ][ttsId] || 'ElevenLabs+Text-to-speech';

        const dynamicLink = `https://docs.google.com/forms/d/e/1FAIpQLSePVGPXnMtGjqAL8d1pF1b6fq416BhPSxWOraa_UdyfSW1q5w/viewform?usp=pp_url&entry.282068203=Website&entry.1753340543=${sttLabel}&entry.1800654359=${llmLabel}&entry.2022851438=${ttsLabel}`;
        
        setFormsLink(dynamicLink);
    }, []);

    return (
        <a
            href={formsLink}
            target="_blank"
            rel="noopener noreferrer"
            className="feedback_button"
            aria-label="Feedback Form"
            title="Feedback Form"
        >
            <Icon 
                className="feedback_button_icon"
                icon={Constants.icons.feedback_form} 
                size={2} 
                altName="Feedback Form" />
        </a>
    );
}

export default FeedbackButton;