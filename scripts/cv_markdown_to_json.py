#!/usr/bin/env python3
"""
Script to convert markdown CV to JSON format
Author: Yuan Chen
"""

import argparse
import glob
import json
import os
import re
from datetime import date, datetime
from pathlib import Path

import yaml


class DateTimeEncoder(json.JSONEncoder):
    """Custom JSON encoder to handle date objects."""

    def default(self, obj):
        if isinstance(obj, (datetime, date)):
            return obj.isoformat()
        return super().default(obj)


def parse_markdown_cv(md_file):
    """Parse a markdown CV file and return section text keyed by section title."""
    with open(md_file, 'r', encoding='utf-8') as file:
        content = file.read()

    # Remove YAML front matter.
    content = re.sub(r'^---\s*\n.*?\n---\s*\n?', '', content, flags=re.DOTALL)

    lines = content.splitlines()
    sections = {}
    current_section = None
    section_content = []
    index = 0

    while index < len(lines):
        raw_line = lines[index]
        stripped_line = raw_line.strip()

        next_index = index + 1
        while next_index < len(lines) and not lines[next_index].strip():
            next_index += 1

        heading_candidate = (
            stripped_line
            and not stripped_line.startswith(('*', '-'))
            and re.search(r'[A-Za-z]', stripped_line) is not None
        )

        is_section_heading = (
            heading_candidate
            and next_index < len(lines)
            and re.fullmatch(r'[-=]{3,}', lines[next_index].strip()) is not None
        )

        if is_section_heading:
            if current_section:
                sections[current_section] = '\n'.join(section_content).strip()
            current_section = stripped_line
            section_content = []
            index = next_index + 1
            continue

        if current_section:
            section_content.append(raw_line)

        index += 1

    if current_section:
        sections[current_section] = '\n'.join(section_content).strip()

    return sections


def get_section_text(sections, aliases):
    """Return the first matching section content for the given aliases."""
    normalized = {key.strip().lower(): value for key, value in sections.items()}
    for alias in aliases:
        value = normalized.get(alias.lower())
        if value and value.strip():
            return value
    return ''


def parse_config(config_file):
    """Parse the Jekyll _config.yml file for additional information."""
    if not config_file or not os.path.exists(config_file):
        return {}

    with open(config_file, 'r', encoding='utf-8') as file:
        config = yaml.safe_load(file)

    return config or {}


def extract_author_info(config):
    """Extract author information from the config file."""
    author_info = {
        'name': config.get('name', ''),
        'email': '',
        'phone': '',
        'website': config.get('url', ''),
        'summary': '',
        'location': {
            'address': '',
            'postalCode': '',
            'city': '',
            'countryCode': 'US',
            'region': '',
        },
        'profiles': [],
    }

    author = config.get('author', {}) if isinstance(config.get('author'), dict) else {}

    if author.get('name'):
        author_info['name'] = author.get('name')
    if author.get('email'):
        author_info['email'] = author.get('email')
    if author.get('location'):
        author_info['location']['city'] = author.get('location', '')
    if author.get('employer'):
        author_info['summary'] = f"Currently employed at {author.get('employer')}"
    if author.get('bio'):
        author_info['summary'] = (
            f"{author_info['summary']}. {author.get('bio')}"
            if author_info['summary']
            else author.get('bio')
        )

    profiles = []

    if author.get('googlescholar'):
        profiles.append({'network': 'Google Scholar', 'username': '', 'url': author.get('googlescholar')})
    if author.get('orcid'):
        profiles.append({'network': 'ORCID', 'username': '', 'url': author.get('orcid')})
    if author.get('researchgate'):
        profiles.append({'network': 'ResearchGate', 'username': '', 'url': author.get('researchgate')})
    if author.get('github'):
        username = author.get('github')
        profiles.append({'network': 'GitHub', 'username': username, 'url': f'https://github.com/{username}'})
    if author.get('linkedin'):
        username = author.get('linkedin')
        profiles.append({'network': 'LinkedIn', 'username': username, 'url': f'https://www.linkedin.com/in/{username}'})
    if author.get('twitter'):
        username = author.get('twitter')
        profiles.append({'network': 'Twitter', 'username': username, 'url': f'https://twitter.com/{username}'})

    author_info['profiles'] = profiles

    return author_info


def parse_date_range(text):
    """Parse common CV date-range strings into start/end years."""
    normalized = text.strip().replace('\u2013', '-').replace('\u2014', '-')

    year_range = re.search(r'(\d{4})\s*-\s*(\d{4}|present)', normalized, re.IGNORECASE)
    if year_range:
        return year_range.group(1), year_range.group(2).lower()

    month_year_range = re.search(
        r'([A-Za-z]{3,9}\s+\d{4})\s*-\s*([A-Za-z]{3,9}\s+\d{4}|present)',
        normalized,
        re.IGNORECASE,
    )
    if month_year_range:
        start_match = re.search(r'(\d{4})', month_year_range.group(1))
        end_group = month_year_range.group(2)
        if re.search(r'present', end_group, re.IGNORECASE):
            end_year = 'present'
        else:
            end_match = re.search(r'(\d{4})', end_group)
            end_year = end_match.group(1) if end_match else ''
        return start_match.group(1) if start_match else '', end_year

    return '', ''


def parse_education(education_text):
    """Parse education section from markdown."""
    education_entries = []
    entries = re.findall(r'\* (.*?)(?=\n\*|\Z)', education_text, re.DOTALL)

    for entry in entries:
        match = re.match(r'([^,]+), ([^,]+), (\d{4})(.*)', entry.strip())
        if not match:
            continue

        degree, institution, year, additional = match.groups()
        gpa_match = re.search(r'GPA: ([\d\.]+)', additional)
        gpa = gpa_match.group(1) if gpa_match else None

        education_entries.append(
            {
                'institution': institution.strip(),
                'area': degree.strip(),
                'studyType': '',
                'startDate': '',
                'endDate': year.strip(),
                'gpa': gpa,
                'courses': [],
            }
        )

    return education_entries


def parse_work_experience(work_text):
    """Parse work experience section from markdown."""
    work_entries = []
    entries = re.findall(r'(?m)^\* (.*?)(?=^\* |\Z)', work_text, re.DOTALL)

    for entry in entries:
        lines = [line.strip() for line in entry.split('\n') if line.strip()]
        if not lines:
            continue

        position = lines[0].rstrip(',').strip()
        company = ''
        start_date = ''
        end_date = ''
        summary_parts = []
        highlights = []

        for line in lines[1:]:
            if line.startswith('*') or line.startswith('-'):
                highlights.append(line[1:].strip())
                continue

            if not company:
                company = line.rstrip(',').strip()
                continue

            if not start_date and not end_date:
                parsed_start, parsed_end = parse_date_range(line)
                if parsed_start or parsed_end:
                    start_date, end_date = parsed_start, parsed_end
                    continue

            summary_parts.append(line)

        work_entries.append(
            {
                'company': company,
                'position': position,
                'website': '',
                'startDate': start_date,
                'endDate': end_date,
                'summary': ' '.join(summary_parts),
                'highlights': highlights,
            }
        )

    return work_entries


def parse_skills(skills_text):
    """Parse skills section from markdown."""
    skills_entries = []
    current = None

    for raw_line in skills_text.splitlines():
        line = raw_line.strip()
        if not line:
            continue

        bullet_category = re.match(r'^\*+\s*([^:]+):\s*(.*)$', line)
        if bullet_category:
            if current:
                current['keywords'] = list(dict.fromkeys(current['keywords']))
                skills_entries.append(current)
            current = {'name': bullet_category.group(1).strip(), 'level': '', 'keywords': []}
            inline = bullet_category.group(2).strip()
            if inline:
                current['keywords'].extend([item.strip() for item in inline.split(',') if item.strip()])
            continue

        plain_category = re.match(r'^([^:]+):\s*(.*)$', line)
        if plain_category and not line.startswith('-') and not line.startswith('*'):
            if current:
                current['keywords'] = list(dict.fromkeys(current['keywords']))
                skills_entries.append(current)
            current = {'name': plain_category.group(1).strip(), 'level': '', 'keywords': []}
            inline = plain_category.group(2).strip()
            if inline:
                current['keywords'].extend([item.strip() for item in inline.split(',') if item.strip()])
            continue

        if not current:
            continue

        if line.startswith('*') or line.startswith('-'):
            value = line[1:].strip()
        else:
            value = line

        if value:
            current['keywords'].extend([item.strip() for item in value.split(',') if item.strip()])

    if current:
        current['keywords'] = list(dict.fromkeys(current['keywords']))
        skills_entries.append(current)

    return skills_entries


def parse_front_matter(content):
    """Return parsed front matter for a markdown document."""
    match = re.match(r'^---\s*(.*?)\s*---', content, re.DOTALL)
    if not match:
        return {}
    front_matter = yaml.safe_load(match.group(1))
    return front_matter or {}


def parse_publications(pub_dir):
    """Parse publications from the _publications directory."""
    publications = []
    if not os.path.exists(pub_dir):
        return publications

    for pub_file in sorted(glob.glob(os.path.join(pub_dir, '*.md'))):
        with open(pub_file, 'r', encoding='utf-8') as file:
            front_matter = parse_front_matter(file.read())

        publications.append(
            {
                'name': front_matter.get('title', ''),
                'publisher': front_matter.get('venue', ''),
                'releaseDate': front_matter.get('date', ''),
                'website': front_matter.get('paperurl', ''),
                'summary': front_matter.get('excerpt', ''),
            }
        )

    return publications


def parse_talks(talks_dir):
    """Parse talks from the _talks directory."""
    talks = []
    if not os.path.exists(talks_dir):
        return talks

    for talk_file in sorted(glob.glob(os.path.join(talks_dir, '*.md'))):
        with open(talk_file, 'r', encoding='utf-8') as file:
            front_matter = parse_front_matter(file.read())

        talks.append(
            {
                'name': front_matter.get('title', ''),
                'event': front_matter.get('venue', ''),
                'date': front_matter.get('date', ''),
                'location': front_matter.get('location', ''),
                'description': front_matter.get('excerpt', ''),
            }
        )

    return talks


def parse_teaching(teaching_dir):
    """Parse teaching from the _teaching directory."""
    teaching = []
    if not os.path.exists(teaching_dir):
        return teaching

    for teaching_file in sorted(glob.glob(os.path.join(teaching_dir, '*.md'))):
        with open(teaching_file, 'r', encoding='utf-8') as file:
            front_matter = parse_front_matter(file.read())

        teaching.append(
            {
                'course': front_matter.get('title', ''),
                'institution': front_matter.get('venue', ''),
                'date': front_matter.get('date', ''),
                'role': front_matter.get('type', ''),
                'description': front_matter.get('excerpt', ''),
            }
        )

    return teaching


def parse_portfolio(portfolio_dir):
    """Parse portfolio items from the _portfolio directory."""
    portfolio = []
    if not os.path.exists(portfolio_dir):
        return portfolio

    for portfolio_file in sorted(glob.glob(os.path.join(portfolio_dir, '*.md'))):
        with open(portfolio_file, 'r', encoding='utf-8') as file:
            front_matter = parse_front_matter(file.read())

        fallback_permalink = f"/portfolio/{Path(portfolio_file).stem}/"
        portfolio.append(
            {
                'name': front_matter.get('title', ''),
                'category': front_matter.get('collection', 'portfolio'),
                'date': front_matter.get('date', ''),
                'url': front_matter.get('permalink', fallback_permalink),
                'description': front_matter.get('excerpt', ''),
            }
        )

    return portfolio


def create_cv_json(md_file, config_file, repo_root, output_file):
    """Create a JSON CV from markdown and other repository data."""
    sections = parse_markdown_cv(md_file)
    config = parse_config(config_file)
    author_info = extract_author_info(config)

    work_text = get_section_text(sections, ['Work experience', 'Professional Experience', 'Experience'])
    skills_text = get_section_text(sections, ['Skills', 'Technical Skills', 'Core Competencies'])
    education_text = get_section_text(sections, ['Education'])

    cv_json = {
        'basics': author_info,
        'work': parse_work_experience(work_text),
        'education': parse_education(education_text),
        'skills': parse_skills(skills_text),
        'languages': config.get('languages', []),
        'interests': config.get('interests', []),
        'references': [],
    }

    cv_json['publications'] = parse_publications(os.path.join(repo_root, '_publications'))
    cv_json['presentations'] = parse_talks(os.path.join(repo_root, '_talks'))
    cv_json['teaching'] = parse_teaching(os.path.join(repo_root, '_teaching'))
    cv_json['portfolio'] = parse_portfolio(os.path.join(repo_root, '_portfolio'))

    with open(output_file, 'w', encoding='utf-8') as file:
        json.dump(cv_json, file, indent=2, cls=DateTimeEncoder)

    print(f'Successfully converted {md_file} to {output_file}')


def main():
    """Main function to parse arguments and run the conversion."""
    parser = argparse.ArgumentParser(description='Convert markdown CV to JSON format')
    parser.add_argument('--input', '-i', required=True, help='Input markdown CV file')
    parser.add_argument('--output', '-o', required=True, help='Output JSON file')
    parser.add_argument('--config', '-c', help='Jekyll _config.yml file')

    args = parser.parse_args()
    repo_root = str(Path(args.input).parent.parent)
    config_file = args.config or os.path.join(repo_root, '_config.yml')

    create_cv_json(args.input, config_file, repo_root, args.output)


if __name__ == '__main__':
    main()
