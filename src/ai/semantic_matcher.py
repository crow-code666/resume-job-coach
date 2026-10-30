
import json
import os

from dotenv import load_dotenv
from groq import Groq
from tavily import TavilyClient


load_dotenv()


class SemanticMatcher:
    """AI career analysis and live job-market research."""

    def __init__(self, model=None):
        groq_key = self._get_key("GROQ_API_KEY")
        tavily_key = self._get_key("TAVILY_API_KEY")

        if not groq_key:
            raise ValueError(
                "GROQ_API_KEY is not configured. Add it to "
                ".streamlit/secrets.toml or your environment variables."
            )

        self.model = (
            model
            or os.getenv("GROQ_MODEL")
            or "openai/gpt-oss-20b"
        )

        self.client = Groq(api_key=groq_key)
        self.search_client = TavilyClient(api_key=tavily_key) if tavily_key else None

    @staticmethod
    def _get_key(name):
        """Read a key from Streamlit secrets first, then environment variables."""
        try:
            import streamlit as st
            value = st.secrets.get(name)
            if value:
                return value
        except Exception:
            pass
        return os.getenv(name)

    def generate_response(self, system_prompt, user_prompt):
        """Generate an AI response using Groq."""

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": system_prompt,
                    },
                    {
                        "role": "user",
                        "content": user_prompt,
                    },
                ],
                temperature=0.3,
                max_completion_tokens=4000,
            )

            content = response.choices[0].message.content

            if not content:
                raise RuntimeError("Groq returned an empty response.")

            return content.strip()

        except Exception as error:
            raise RuntimeError(
                f"Groq API request failed: {error}"
            ) from error

    def search_web(self, query, max_results=5):
        """Search the web using Tavily."""

        if self.search_client is None:
            raise ValueError(
                "TAVILY_API_KEY is not configured. Add it to "
                ".streamlit/secrets.toml or your environment variables "
                "to use live market research."
            )

        try:
            response = self.search_client.search(
                query=query,
                search_depth="basic",
                topic="general",
                max_results=max_results,
                include_answer=False,
            )

            results = []

            for item in response.get("results", []):
                results.append({
                    "title": item.get("title", "Untitled"),
                    "url": item.get("url", ""),
                    "content": item.get("content", "")[:1800],
                    "score": item.get("score"),
                })

            return results

        except Exception as error:
            raise RuntimeError(
                f"Tavily web search failed: {error}"
            ) from error

    def research_job_market(self, job_description):
        """
        Infer the target role, search current web results,
        and use Groq to analyze the collected information.
        """

        if not job_description.strip():
            raise ValueError("Job description cannot be empty.")

        if self.search_client is None:
            raise ValueError(
                "TAVILY_API_KEY is not configured. Add it to "
                ".streamlit/secrets.toml or your environment variables "
                "to use live market research."
            )

        # Step 1: Identify the target role.
        role_prompt = """
Identify the main job title from the supplied job description.

Return only the job title.
Do not add explanations.
If the title is unclear, return the most likely role.
"""

        job_role = self.generate_response(
            role_prompt,
            job_description[:12000],
        )

        # Step 2: Search India and global job markets.
        queries = [
            f"{job_role} job openings India required skills 2026",
            f"{job_role} jobs global careers required skills 2026",
            f"{job_role} company careers job description technologies 2026",
        ]

        all_results = []
        seen_urls = set()

        for query in queries:
            search_results = self.search_web(
                query=query,
                max_results=5,
            )

            for result in search_results:
                url = result["url"]

                if url and url not in seen_urls:
                    seen_urls.add(url)
                    all_results.append(result)

        if not all_results:
            raise RuntimeError(
                "No web search results were returned. "
                "Try another job description or check your Tavily account."
            )

        # Step 3: Prepare source material for Groq.
        source_text = []

        for index, result in enumerate(all_results, start=1):
            source_text.append(
                f"""
SOURCE {index}
Title: {result['title']}
URL: {result['url']}
Information:
{result['content']}
"""
            )

        research_data = "\n".join(source_text)

        # Step 4: Ask Groq to analyze the real search results.
        system_prompt = """
You are an expert global technology recruiter,
job-market researcher, and career preparation assistant.

You receive:
1. A candidate's target job description.
2. Search results collected from the live internet.

Analyze only what the supplied information supports.

Important rules:
- Never invent job vacancies.
- Never invent company names or application links.
- Distinguish the supplied job description from market findings.
- Do not treat search snippets as fully verified facts.
- Mention when information is incomplete.
- Separate India findings from global findings.
- Identify repeated technologies and skills across sources.
- Do not claim a company is hiring unless a source supports it.
- Provide source URLs for relevant findings.
"""

        user_prompt = f"""
TARGET JOB ROLE:
{job_role}

ORIGINAL JOB DESCRIPTION:
{job_description[:12000]}

LIVE WEB SEARCH RESULTS:
{research_data}

Prepare a detailed report with these sections:

1. Target Role Overview

2. Skills Required by the Supplied Job Description

Separate technical skills, soft skills, responsibilities,
tools, technologies, and qualifications.

3. India Job Market Findings

Identify skills and technologies mentioned in the
search results relevant to Indian opportunities.

4. Global Job Market Findings

Identify skills and technologies mentioned in the
international search results.

5. Most Frequently Appearing Technical Skills

Group related skills and explain their importance.
Do not invent frequency statistics.

6. Additional Technologies Worth Learning

Distinguish market trends from requirements in
the supplied job description.

7. Common Experience and Qualification Requirements

8. Important Resume Keywords

9. Recommended Practical Projects

10. Candidate Learning Roadmap

11. Job Search Results

List the relevant search-result titles, their URLs,
and a brief explanation of their relevance.

12. Research Limitations

Explain which findings need confirmation on the
original company career page.

Use beginner-friendly explanations.
"""

        report = self.generate_response(
            system_prompt,
            user_prompt,
        )

        return {
            "job_role": job_role,
            "report": report,
            "sources": all_results,
            "queries": queries,
        }

    def analyze_job_description(self, job_description):
        """Analyze a supplied job description."""

        system_prompt = """
You are an expert recruitment analyst and career coach.

Analyze job descriptions carefully.

Separate mandatory and preferred requirements.
Explain technical terms in beginner-friendly language.
Do not invent company policies or requirements.
"""

        user_prompt = f"""
Analyze this job description:

{job_description}

Include:

1. Job overview
2. Responsibilities
3. Mandatory technical skills
4. Preferred technical skills
5. Languages and frameworks
6. Tools and platforms
7. Educational qualifications
8. Experience requirements
9. Fresher eligibility
10. Resume keywords
11. Interview topics
12. Practical project recommendations
13. Learning roadmap
"""

        return self.generate_response(
            system_prompt,
            user_prompt,
        )

    def research_role(self, job_role, market="both"):
        """Research a job role using its own search queries."""

        if market.lower() == "india":
            queries = [
                f"{job_role} jobs India required skills 2026",
                f"{job_role} company careers India 2026",
            ]

        elif market.lower() == "global":
            queries = [
                f"{job_role} jobs worldwide required skills 2026",
                f"{job_role} company careers global 2026",
            ]

        else:
            queries = [
                f"{job_role} jobs India required skills 2026",
                f"{job_role} jobs global careers required skills 2026",
                f"{job_role} company careers technologies 2026",
            ]

        results = []

        for query in queries:
            results.extend(
                self.search_web(query, max_results=5)
            )

        unique_results = []
        seen = set()

        for result in results:
            if result["url"] and result["url"] not in seen:
                seen.add(result["url"])
                unique_results.append(result)

        source_text = "\n\n".join(
            f"Title: {r['title']}\nURL: {r['url']}\n{r['content']}"
            for r in unique_results
        )

        report = self.generate_response(
            "You are a job-market researcher. "
            "Analyze the supplied live search results. "
            "Do not invent vacancies, salaries, or hiring facts.",
            f"""
Research this job role: {job_role}
Market: {market}

Search results:
{source_text}

Explain:
1. Job responsibilities
2. Common required skills
3. Preferred skills
4. Technologies and frameworks
5. Qualifications and experience
6. Interview topics
7. Projects to build
8. Learning roadmap
9. Relevant job search sources and URLs

Distinguish verified source information from general advice.
""",
        )

        return {
            "job_role": job_role,
            "report": report,
            "sources": unique_results,
            "queries": queries,
        }

    def research_job_skills(self, job_description, max_results=5):
        """
        Search current job-market sources for skills relevant to a supplied JD.

        The response keeps requirements from the supplied JD separate from
        skills supported by the retrieved online sources.
        """
        if not job_description or not job_description.strip():
            raise ValueError("Job description cannot be empty.")

        if self.search_client is None:
            raise ValueError(
                "TAVILY_API_KEY is not configured. Add it to "
                ".streamlit/secrets.toml or your environment variables "
                "to use online skill research."
            )

        role_prompt = """
Identify the main job title in this job description.
Return only the job title, without explanation.
If the title is unclear, choose the closest role supported by the text.
"""
        job_role = self.generate_response(
            role_prompt,
            job_description[:12000],
        ).strip()

        queries = [
            f'"{job_role}" job postings required skills technologies India 2026',
            f'"{job_role}" company careers job description required skills global 2026',
            f'"{job_role}" hiring requirements tools frameworks qualifications 2026',
        ]

        results = []
        seen_urls = set()
        for query in queries:
            for item in self.search_web(query, max_results=max_results):
                url = item.get("url", "").strip()
                if url and url not in seen_urls:
                    seen_urls.add(url)
                    results.append(item)

        if not results:
            raise RuntimeError(
                "The web search returned no usable sources for this role. "
                "Try again or check your Tavily account."
            )

        source_text = "\n\n".join(
            f"SOURCE {index}\n"
            f"Title: {item.get('title', 'Untitled')}\n"
            f"URL: {item.get('url', '')}\n"
            f"Extract: {item.get('content', '')}"
            for index, item in enumerate(results, start=1)
        )

        system_prompt = """
You are a careful job-market researcher and skills analyst.
Use the supplied job description and retrieved web-search source excerpts.

Return ONLY one valid JSON object. Do not use Markdown or code fences.
Do not invent skills, qualifications, companies, vacancies, or statistics.

Keep the two evidence sets separate:
- JD arrays must contain skills explicitly required or preferred by the supplied JD.
- Market arrays must contain skills supported by the retrieved job-posting or company-career source excerpts.
- Do not copy a JD skill into the market arrays unless the online excerpts also support it.
- If evidence is insufficient, return an empty array rather than guessing.
- Use concise skill/tool names, not sentences.
- Distinguish required from preferred only when the source supports that distinction.

Use exactly these keys:
{
  "job_role": "string",
  "jd_required_skills": ["string"],
  "jd_preferred_skills": ["string"],
  "market_required_skills": ["string"],
  "market_preferred_skills": ["string"],
  "market_tools_and_platforms": ["string"],
  "market_insights": ["short evidence-based observation"],
  "research_limitations": "short string"
}
"""
        user_prompt = f"""
JOB DESCRIPTION SUPPLIED BY THE USER:
{job_description[:12000]}

LIVE WEB SEARCH EXCERPTS:
{source_text}

Identify:
1. Technical skills and technologies required by the supplied JD.
2. Preferred skills in the supplied JD.
3. Skills explicitly supported by the online sources for comparable roles.
4. Tools and platforms found in those sources.
5. A few short observations grounded in the supplied excerpts.

Do not claim that a search excerpt proves a vacancy is still open.
Do not create frequency counts unless they can be calculated directly
from the provided source excerpts.
"""
        raw = self.generate_response(system_prompt, user_prompt).strip()
        cleaned = raw
        if cleaned.startswith("```"):
            cleaned = cleaned.split("\n", 1)[-1]
            if cleaned.endswith("```"):
                cleaned = cleaned[:-3].strip()

        try:
            data = json.loads(cleaned)
        except json.JSONDecodeError:
            start = cleaned.find("{")
            end = cleaned.rfind("}")
            if start < 0 or end <= start:
                raise RuntimeError(
                    "AI returned an unreadable skills report. Please run the research again."
                )
            try:
                data = json.loads(cleaned[start:end + 1])
            except json.JSONDecodeError as error:
                raise RuntimeError(
                    "AI returned an unreadable skills report. Please run the research again."
                ) from error

        def clean_list(value):
            if not isinstance(value, list):
                return []
            cleaned_items = []
            seen = set()
            for entry in value:
                if not isinstance(entry, str):
                    continue
                item = " ".join(entry.split()).strip(" •-")
                key = item.casefold()
                if item and len(item) <= 80 and key not in seen:
                    seen.add(key)
                    cleaned_items.append(item)
            return cleaned_items[:40]

        jd_required = clean_list(data.get("jd_required_skills"))
        jd_preferred = clean_list(data.get("jd_preferred_skills"))
        market_required = clean_list(data.get("market_required_skills"))
        market_preferred = clean_list(data.get("market_preferred_skills"))
        market_tools = clean_list(data.get("market_tools_and_platforms"))
        insights = clean_list(data.get("market_insights"))

        jd_all = {item.casefold() for item in jd_required + jd_preferred}
        market_all = market_required + market_preferred + market_tools
        market_all_unique = clean_list(market_all)
        shared = [
            item for item in market_all_unique
            if item.casefold() in jd_all
        ]
        additional = [
            item for item in market_all_unique
            if item.casefold() not in jd_all
        ]

        return {
            "job_role": str(data.get("job_role") or job_role).strip(),
            "jd_required_skills": jd_required,
            "jd_preferred_skills": jd_preferred,
            "market_required_skills": market_required,
            "market_preferred_skills": market_preferred,
            "market_tools_and_platforms": market_tools,
            "shared_skills": shared,
            "additional_market_skills": additional,
            "market_insights": insights,
            "research_limitations": str(
                data.get("research_limitations") or
                "Search summaries are preliminary. Check the original job and company career pages."
            ),
            "sources": results,
            "queries": queries,
        }

