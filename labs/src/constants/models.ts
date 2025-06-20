// models settings
import React from 'react';
import * as Constants from './index.ts';

//interfaces
interface ModelProps {
    id: number;
    name: string;
    icon: string;
    description: string;
    stt: number;
    llm: number;
    tts: number;
    language: number;
}

interface STTProps { id: number; name: string; icon: string; }
interface LLMProps { id: number; name: string; icon: string; }
interface TTSProps { id: number; name: string; icon: string; }
interface LanguageProps { id: number; name: string; icon: string; }

// configs to identify everything needed to run a model pipeline
interface ConfigParams {
    model: number;
    stt: number;
    llm: number;
    tts: number;
    language: number;
}

// models settings
const models: ModelProps[] = [
    {
        id: 0,
        name: "Orion",
        icon: Constants.icons.triangle_points,
        description: "Our prototype model with experimental features",
        stt: 0,
        llm: 0,
        tts: 2,
        language: 0,
    },
    {
        id: 1,
        name: "Custom",
        icon: Constants.icons.pencil,
        description: "Combine any components to create a custom model experience",
        stt: 0,
        llm: 0,
        tts: 2,
        language: 0,
    },
];

const sttOptions: STTProps[] = [
    {
        id: 0,
        name: "Google Speech-to-text (batch)",
        icon: Constants.icons.google_stt,
    },
    {
        id: 2,
        name: "Amazon Transcribe",
        icon: Constants.icons.aws, // couldnt find a good icon for amazon transcribe ;_;
    },
    {
        id: 3,
        name: "ElevenLabs Speech-to-text",
        icon: Constants.icons.elevenlabs,
    },
    {
        id: 4,
        name: "Azure Speech-to-text",
        icon: Constants.icons.azure, // couldnt find a good icon either :(
    },
    {
        id: 5,
        name: "Faster Whisper (tiny-pt-default)",
        icon: Constants.icons.faster_whisper_stt
    },
    {
        id: 6,
        name: "Faster Whisper (small-pt-MyNorthAI)",
        icon: Constants.icons.faster_whisper_stt
    }
]

const llmOptions: LLMProps[] = [
    {
        id: 0,
        name: "Gemini (2-0 flash)",
        icon: Constants.icons.gemini_llm,
    },
    {
        id: 1,
        name: "ChatGPT (4o)",
        icon: Constants.icons.chatgpt_llm,
    }
]
const ttsOptions: TTSProps[] = [
    {
        id: 0,
        name: "Google text-to-speech",
        icon: Constants.icons.google_tts,
    },
    {
        id: 1,
        name: "Amazon Polly",
        icon: Constants.icons.amazon_polly,
    },
    {
        id: 2,
        name: "ElevenLabs text-to-speech",
        icon: Constants.icons.elevenlabs
    },
    {
        id: 3,
        name: "Azure Speech SDK",
        icon: Constants.icons.azure
    },
    {
        id: 4,
        name: "Piper TTS (pt_PT-tugão-medium)",
        icon: Constants.icons.piper_tts
    },
    {
        id: 5,
        name: "Microsoft Edge TTS",
        icon: Constants.icons.microsoft_edge_tts
    }
]

const languageOptions: LanguageProps[] = [
    {
        id: 0,
        name: "Portuguese (Portugal)",
        icon: Constants.icons.flag_portugal,
    }
]

const getNames = <T extends { name: string }>(items: T[]): string[] =>
    items.map(item => item.name);
  
const getIcons = <T extends { icon: string }>(items: T[]): string[] =>
    items.map(item => item.icon);
  
//extract just the names and icons fields from the lists, for dropdown representation
const paramsNames = {
    model: getNames(Object.values(models)),
    stt: getNames(sttOptions),
    llm: getNames(llmOptions),
    tts: getNames(ttsOptions),
    language: getNames(languageOptions),
}

const paramsIcons = {
    model: getIcons(Object.values(models)),
    stt: getIcons(sttOptions),
    llm: getIcons(llmOptions),
    tts: getIcons(ttsOptions),
    language: getIcons(languageOptions),
}

export {models,sttOptions,llmOptions,ttsOptions,languageOptions, paramsNames, paramsIcons}
export type {ModelProps, STTProps, LLMProps, TTSProps, LanguageProps, ConfigParams}
export default models;