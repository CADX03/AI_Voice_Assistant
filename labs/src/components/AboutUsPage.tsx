import React, { useState, useEffect } from 'react';
import Header from './Header';
import './AboutUsPage.css'; 
import * as Constants from '../constants/index.ts';
import FeedbackButton from './FeedbackButton.tsx';

const aboutSectionsData = [
    {
        title: "Our Story",
        summary: "Discover how Voice Future began, driven by a vision to revolutionize customer interaction with intelligent voice solutions.",
        fullContent: "Voice Future was founded with the vision of revolutionizing customer interaction through intelligent voice solutions. We believe in the power of technology to create more efficient, human, and accessible communication channels. Our journey began with a small team of passionate innovators dedicated to pushing the boundaries of what's possible in voice AI."
    },
    {
        title: "Our Mission",
        summary: "Learn about our commitment to empowering businesses with cutting-edge voice assistant technology for enhanced experiences.",
        fullContent: "Our mission is to empower businesses with cutting-edge voice assistant technology that enhances customer experience, streamlines operations, and drives growth. We strive to deliver solutions that are not only technologically advanced but also intuitive and easy to integrate."
    },
    {
        title: "The Team",
        summary: "Meet the diverse and experienced minds behind Voice Future, united by a passion for excellence and voice innovation.",
        fullContent: "Meet the minds behind Voice Future. Our team comprises experienced software engineers, UX designers, and business strategists, all working together to build the future of voice. We are a diverse group united by our commitment to excellence and innovation."
    },
    {
        title: "Why Voice Future?",
        summary: "Understand our commitment to service excellence, adaptable technology, and meeting evolving market demands.",
        fullContent: "We are committed to providing a service of excellence, focused on the needs of our clients. Our technology is designed to be adaptable and scalable, ensuring that we can meet the evolving demands of the market. Explore our LABS to see our technology in action."
    }
];

const AboutUsPage: React.FC = () => {
    const [selectedSection, setSelectedSection] = useState(aboutSectionsData[0]);
    const [scrollY, setScrollY] = useState(0); 

    useEffect(() => {
        const handleScroll = () => {
            setScrollY(window.scrollY);
        };

        window.addEventListener('scroll', handleScroll, { passive: true });
        return () => window.removeEventListener('scroll', handleScroll);
    }, []);
    
    const bannerElement = document.querySelector('.labspage_banner_section');
    const bannerHeight = bannerElement ? bannerElement.clientHeight : 0;
    const isHeaderAtTop = scrollY > bannerHeight;


    return (
        <>
            <Header isHeaderAtTop={isHeaderAtTop} />
            <div className='labspage_container aboutuspage_container'> 
                
                <div className='labspage_banner_section'>
                    <img src={Constants.images.banner} alt="Voice Future LABS banner" /> 
                    <div className='labspage_banner_text'>
                        <div className='labspage_banner_title'>
                            <span>About Us</span>
                        </div>
                        <div className='labspage_banner_subtitle'>
                            <span>Discover the story, mission, and people behind Voice Future.</span>
                        </div>
                    </div> 
                </div>
                
                <div className='about_us_content_area'>
                    <div className='about_us_cards_container'>
                        {aboutSectionsData.map((section, index) => (
                            <div 
                                key={index} 
                                className={`about_us_topic_card ${selectedSection.title === section.title ? 'selected' : ''}`}
                                onClick={() => setSelectedSection(section)}
                            >
                                <span className='card_title'>{section.title}</span>
                                <p className='card_summary'>{section.summary}</p>
                            </div>
                        ))}
                    </div>

                    {selectedSection && (
                        <div className='about_us_detailed_text_container'>
                            <h2 className='detailed_title'>{selectedSection.title}</h2>
                            <p className='detailed_content'>{selectedSection.fullContent}</p>
                        </div>
                    )}
                </div>

                <FeedbackButton />
            </div>
        </>
    );
};

export default AboutUsPage;