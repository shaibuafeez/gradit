import random
import datetime
from models import db, User, Course, Essay

def add_sample_essays_if_needed():
    """Add sample essays for demonstration purposes"""
    # Check if essays already exist
    if Essay.query.count() > 0:
        return
    
    # Get student and teacher users
    student = User.query.filter_by(email='student@example.com').first()
    teacher = User.query.filter_by(email='teacher@example.com').first()
    
    if not student or not teacher:
        return
    
    # Get courses
    courses = Course.query.all()
    if not courses:
        return
    
    # Sample essay prompts
    prompts = [
        'Discuss the impact of climate change on global ecosystems.',
        'Analyze the themes of identity and belonging in modern literature.',
        'Compare and contrast the economic policies of two major countries.',
        'Evaluate the role of technology in modern education.',
        'Examine the ethical implications of artificial intelligence in healthcare.'
    ]
    
    # Sample essay titles
    titles = [
        'The Effects of Climate Change on Biodiversity',
        'Identity and Belonging in Contemporary Fiction',
        'Economic Policy Comparison: USA vs. China',
        'Technology\'s Role in Transforming Education',
        'AI in Healthcare: Ethical Considerations'
    ]
    
    # Sample essay content (shortened for brevity)
    content_template = """
    Introduction:
    {intro}
    
    Main Body:
    {body_1}
    
    {body_2}
    
    {body_3}
    
    Conclusion:
    {conclusion}
    """
    
    intros = [
        'This essay explores the critical issue of climate change and its far-reaching impacts on global ecosystems.',
        'In contemporary literature, the themes of identity and belonging have become increasingly prominent.',
        'This analysis compares the economic approaches of two major global powers.',
        'The integration of technology in education has revolutionized teaching and learning methodologies.',
        'As artificial intelligence advances in healthcare, numerous ethical questions arise.'
    ]
    
    body_paragraphs = [
        'The evidence for climate change is overwhelming, with rising temperatures, melting ice caps, and extreme weather events.',
        'Many authors explore identity through characters who struggle with cultural displacement and societal expectations.',
        'The United States follows a more market-oriented approach, while China employs a mixed economic system with significant state control.',
        'Online learning platforms have democratized access to education, allowing students from diverse backgrounds to access quality resources.',
        'AI diagnostic tools can process vast amounts of medical data faster than human practitioners, potentially leading to earlier and more accurate diagnoses.'
    ]
    
    conclusions = [
        'In conclusion, addressing climate change requires immediate global cooperation and policy changes.',
        'The exploration of identity and belonging in literature reflects our collective search for meaning in an increasingly complex world.',
        'Both economic systems have strengths and weaknesses, and their effectiveness depends on specific contexts and goals.',
        'While technology offers tremendous benefits to education, it must be implemented thoughtfully to address equity concerns.',
        'The ethical framework for AI in healthcare must balance innovation with patient safety, privacy, and human oversight.'
    ]
    
    # Create sample essays
    for i in range(10):  # Create 10 sample essays
        # Randomly select course, prompt, and title
        course = random.choice(courses)
        prompt_index = i % len(prompts)  # Cycle through prompts
        
        # Generate essay content
        essay_content = content_template.format(
            intro=intros[prompt_index],
            body_1=body_paragraphs[prompt_index],
            body_2='Further analysis shows that this issue has multiple dimensions that need careful consideration.',
            body_3='Research indicates that addressing this challenge requires a multidisciplinary approach.',
            conclusion=conclusions[prompt_index]
        )
        
        # Determine if essay should be graded
        is_graded = (i < 7)  # 7 out of 10 essays are graded
        
        # Create submission date (spread over the last 30 days)
        days_ago = random.randint(1, 30)
        submission_date = datetime.datetime.utcnow() - datetime.timedelta(days=days_ago)
        
        # Create essay
        essay = Essay(
            student_id=student.id,
            title=titles[prompt_index],
            content=essay_content,
            prompt=prompts[prompt_index],
            course_id=course.id,
            submitted_at=submission_date,
            is_graded=is_graded
        )
        
        # Add scores for graded essays
        if is_graded:
            essay.grammar_score = random.uniform(65, 95)
            essay.content_score = random.uniform(70, 98)
            essay.structure_score = random.uniform(75, 95)
            essay.overall_score = (essay.grammar_score + essay.content_score + essay.structure_score) / 3
            essay.feedback = 'Good work overall. Pay attention to grammar and structure. Your arguments are well-developed.'
            essay.teacher_reviewed = True
            essay.teacher_id = teacher.id
        
        db.session.add(essay)
    
    db.session.commit()
    print('Added sample essays for demonstration')
