import React, { useState, useEffect } from 'react';
import Header from './Header';
import './UseCasePage.css'
import * as Constants from '../constants/index.ts';
import FeedbackButton from './FeedbackButton.tsx';

const useCases = [
    {
        title: 'Use Case 1',
        subtitle: 'Return products',
        description: 'Para podermos tratar da sua devolução, indique por favor o número da encomenda, a descrição dos artigos que pretende devolver e as respetivas quantidades.',
        userExample: 'Quero devolver uma encomenda!',
        aiExample: 'Primeiro preciso do número da encomenda.<br/>Pode dizer qual é o número da sua encomenda?'
    },
    {
        title: 'Use Case 2',
        subtitle: 'Reschedule deliveries',
        description: 'Para reagendarmos a sua entrega, precisamos do número da encomenda e de saber a sua disponibilidade, com a indicação de uma restrição mínima de 24 horas.',
        userExample: 'Quero reagendar uma entrega!',
        aiExample: 'Claro! Pode indicar o número da sua encomenda e <br/>quais os dias/horários mais convenientes para si?'
    },
    {
        title: 'Use Case 3',
        subtitle: 'Others (that fall inside the FAQs scope)',
        description: 'Para podermos ajudar, indique por favor o número da sua encomenda. Caso não tenha, partilhe o email associado à sua conta Continente Online.',
        userExample: 'Preciso de ajuda com a minha conta.',
        aiExample: 'Claro! Pode indicar o número da sua encomenda ou <br/>o email associado à sua conta Continente Online?'
    }
];

const UseCasesPage: React.FC = () => {
    const [selectedUseCase, setSelectedUseCase] = useState(useCases[0]);

    useEffect(() => {
        const handleScroll = () => {
            //setIsHeaderAtTop(window.scrollY < 50);
        };

        window.addEventListener('scroll', handleScroll);
        return () => window.removeEventListener('scroll', handleScroll);
    }, []);

    const isHeaderAtTop = scrollY > (document.querySelector('.labspage_banner_section')?.clientHeight || 0);

    return (
        <>
            <Header isHeaderAtTop={isHeaderAtTop}/>
            <div className='labspage_container'>
                <div className='labspage_banner_section'>
                    <img src={Constants.images.banner}  alt="Voice Future LABS banner" />
                    <div className='labspage_banner_text'>
                        <div className='labspage_banner_title'>
                            <span>Use Cases</span>
                        </div>
                        <div className='labspage_banner_subtitle'>
                            <span>Here, you can explore various use cases to test 
                                <br></br> and experience our application.
                            </span>
                        </div>
                    </div>
                </div>
                <div className='use_cases'>
                    {useCases.map((useCase, index) => (
                        <div
                            key={index}
                            className={`use_case_card ${selectedUseCase.title === useCase.title ? 'selected' : ''}`}
                            onClick={() => setSelectedUseCase(useCase)}
                            style={{ cursor: 'pointer', border: selectedUseCase.title === useCase.title ? '2px solid #021D2C' : '1px solid #ccc' }}
                        >
                            <span className='title'>{useCase.title}</span>
                            <span className='sub_title'>{useCase.subtitle}</span>
                            <p>{useCase.description}</p>
                        </div>
                    ))}

                    <br />
                    <span className='title'>Example of usage</span>
                    <br />
                    <br />
                    <div className='chat-bubble'>
                        <div className='user_text'>
                            <span className='label'>User</span>
                            <br />
                            {selectedUseCase.userExample}
                        </div>
                        <br />
                        <div className='ai_text'>
                            <span className='label'>Voice Future</span>
                            <br />
                            <span dangerouslySetInnerHTML={{ __html: selectedUseCase.aiExample }} />
                        </div>
                    </div>
                </div>
                <FeedbackButton />
            </div>
            
            
        </>
    );
};

export default UseCasesPage;
