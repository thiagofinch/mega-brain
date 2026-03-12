#!/usr/bin/env python3
"""
Complete Tag Matching Script - DE-PARA 1-a-1
Matches each untagged file to its correct planilha entry and applies TAG
"""

import os
import re
import json
from difflib import SequenceMatcher

# Planilha data - extracted from Google Sheets
PLANILHA_DATA = {
    "30 Days Challenge": {
        "prefix": "30DC",
        "entries": {
            "1 - Day 1": "30DC-0001",
            "2 - Day 2": "30DC-0002",
            "3 - Day 3": "30DC-0003",
            "4 - Day 4": "30DC-0004",
            "5 - Day 5": "30DC-0005",
            "6 - Day 6": "30DC-0006",
            "7 - Day 7": "30DC-0007",
            "8 - Day 8": "30DC-0008",
            "9 - Day 9": "30DC-0009",
            "10 - Day 10": "30DC-0010",
            "11 - Day 11.": "30DC-0011",
            "12 - Day 12.": "30DC-0012",
            "13- Day 13.": "30DC-0013",
            "14 - Day 14.": "30DC-0014",
            "15 - Day 15": "30DC-0015",
            "16 - Day 16": "30DC-0016",
            "17 - Day 17": "30DC-0017",
            "18 - Day 18": "30DC-0018",
            "19 - Day 19": "30DC-0019",
            "20 - Day 20": "30DC-0020",
            "21 - Day 21": "30DC-0021",
            "22 - Day 22": "30DC-0022",
            "23 - Day 23": "30DC-0023",
            "24 - Day 24": "30DC-0024",
            "25 - Day 25": "30DC-0025",
            "26 - Day 26": "30DC-0026",
            "27 - Day 27": "30DC-0027",
            "28 - Day 28": "30DC-0028",
            "29 - Day 29.": "30DC-0029",
            "30 - Day 30": "30DC-0030",
        }
    },
    "Cold Video Pitch": {
        "prefix": "PCVP",
        "entries": {
            "1. Power Of Cold Video.": "PCVP-0001",
            "2. Selling Advertising.": "PCVP-0002",
            "3. Social Media Management.": "PCVP-0003",
            "4. Google PPC.": "PCVP-0004",
            "5. Facebook And Instagram.": "PCVP-0005",
            "6. Long Form Content Creation.": "PCVP-0006",
            "7. Animation.": "PCVP-0007",
            "8. Graphics Design.": "PCVP-0008",
            "9. Google Listing.": "PCVP-0009",
            "10. Redoing Thumbnails.": "PCVP-0010",
            "11. Sell Funnels.": "PCVP-0011",
            "12. Chatbots.": "PCVP-0012",
            "13. PR Services.": "PCVP-0013",
        }
    },
    "Agency Blueprint": {
        "prefix": "AOBA",
        "entries": {
            "1. What Is A Marketing Agency.": "AOBA-0001",
            "2. Phases Of A Marketing Agency.": "AOBA-0002",
            "3. Skills Or No Skills.": "AOBA-0003",
            "4. Is It Best To Have Stuff Or A Referral Network.": "AOBA-0004",
            "5. What Are The Possible Limiting Beliefs.": "AOBA-0005",
            "6. What Is PPHD.": "AOBA-0006",
            "7. Leveraging The Facebook Group.": "AOBA-0007",
            "8. Is It Best To Go General Or Niche.": "AOBA-0008",
            "9. Whats The Best Business Model Service Clients Or Consulting.": "AOBA-0009",
            "10. How To Keep A Real Perspective Of Things.": "AOBA-0010",
            "11. Do You Need A Website For Your Agency.": "AOBA-0011",
            "12. How To Become An Expert.": "AOBA-0012",
            "13. Before You Even Think About Getting A Partner.": "AOBA-0013",
            "14. How To Be Comfortable With Failure.": "AOBA-0014",
            "15. Anatomy Of A Perfect Client.": "AOBA-0015",
            "16. How To Keep Your Standards High.": "AOBA-0016",
            "17. The Power Of Expert Positioning": "AOBA-0017",
            "18. How To Improve Your Social Presence.": "AOBA-0018",
            "19. The Best Way To Hijack Authority.": "AOBA-0019",
            "20. Differences Between Hard Flex and Soft Flex.": "AOBA-0020",
            "21. When To Ask For Testimonials.": "AOBA-0021",
            "22. Every Result Is A Marketable Headline.": "AOBA-0022",
            "23. How To PR For Expansion.": "AOBA-0023",
            "24. How To Overcome Major Obstacles.": "AOBA-0024",
            "25. Is It Better To Charge High-Ticket Or Competitive Pricing.": "AOBA-0025",
            "26. What Are The Core Services To Offer.": "AOBA-0026",
            "27. What Model Is Better Transactional Or Recurring.": "AOBA-0027",
            "28. How To Move From Transactional To Recurring.": "AOBA-0028",
            "29. How To Stay Away From Free To Paid Service.": "AOBA-0029",
            "30. The Profit First Business Model.": "AOBA-0030",
            "31. How To Manage Agency Costs.": "AOBA-0031",
            "32. How To Setup Bank Accounts.": "AOBA-0032",
            "33. State Of The Agency Contraction And Expansion.": "AOBA-0033",
            "34. Refunds Policy No Refunds.": "AOBA-0034",
            "35. Result-Driven Services.": "AOBA-0035",
            "36. Is It Better To Have A Contract Or Not.": "AOBA-0036",
            "37. Change Is The Only Constant.": "AOBA-0037",
            "38. Is It Best To Get New Skills Or Referrals.": "AOBA-0038",
            "39. Cash Is Like Oxygen.": "AOBA-0039",
            "40. Why Big Companies Focus On Sales.": "AOBA-0040",
            "41. Daily Attitude And Training": "AOBA-0041",
            "42. How Your Outflow Equals Your Inflow.": "AOBA-0042",
            "43. Money Is In The Follow Up.": "AOBA-0043",
            "44. How To Use Conviction To Win More.": "AOBA-0044",
            "45. How To Win The Sales Game.": "AOBA-0045",
            "46. Duplicating Yourself With Sales People.": "AOBA-0046",
            "47. How To Be Confident In Your Services.": "AOBA-0047",
            "48. How To Keep Your Cool At All Times.": "AOBA-0048",
            "49. Is Cold Calling Dead.": "AOBA-0049",
            "50. How To Keep A Full Pipeline.": "AOBA-0050",
            "51. When Is It Time To Fire A Client.": "AOBA-0051",
            "52. How To Deal With More Rejection Than Acceptance": "AOBA-0052",
            "53. What Is A VAK.": "AOBA-0053",
            "54. Leverage The Power Of Math.": "AOBA-0054",
            "55. How To Use Systems To Save Your Agency.": "AOBA-0055",
            "56. How To Keep Your Team Accountable.": "AOBA-0056",
            "57. Expectations Equal Success.": "AOBA-0057",
        }
    }
}

def normalize_name(name):
    """Normalize filename for matching"""
    # Remove extension
    name = re.sub(r'\.(txt|docx|mp4|pdf)$', '', name, flags=re.IGNORECASE)
    # Remove youtube references
    name = re.sub(r'\s*\[youtube\.com.*?\]', '', name)
    # Remove timestamps
    name = re.sub(r'\s*\d{1,2}-\d{1,2}-\d{2,4}', '', name)
    # Normalize spaces and case
    name = name.strip().lower()
    # Remove multiple spaces
    name = re.sub(r'\s+', ' ', name)
    return name

def find_best_match(filename, threshold=0.7):
    """Find best matching planilha entry for a filename"""
    norm_file = normalize_name(filename)

    best_match = None
    best_score = 0
    best_tag = None
    best_source = None

    for source, data in PLANILHA_DATA.items():
        for entry_name, tag in data["entries"].items():
            norm_entry = normalize_name(entry_name)
            score = SequenceMatcher(None, norm_file, norm_entry).ratio()

            if score > best_score:
                best_score = score
                best_match = entry_name
                best_tag = tag
                best_source = source

    if best_score >= threshold:
        return {
            "matched_to": best_match,
            "tag": best_tag,
            "source": best_source,
            "score": best_score
        }
    return None

def get_untagged_files(inbox_path):
    """Get all untagged .txt files"""
    untagged = []

    for root, dirs, files in os.walk(inbox_path):
        # Skip hidden and backup folders
        dirs[:] = [d for d in dirs if not d.startswith('.') and not d.startswith('_')]

        for f in files:
            if f.endswith('.txt') and not (f.startswith('[') and ']' in f):
                full_path = os.path.join(root, f)
                rel_path = full_path.replace(inbox_path + '/', '')
                untagged.append({
                    "filename": f,
                    "full_path": full_path,
                    "rel_path": rel_path
                })

    return untagged

def main():
    inbox_path = "inbox"

    print("=== COMPLETE TAG MATCHING - DE-PARA 1-a-1 ===\n")

    # Get untagged files
    untagged = get_untagged_files(inbox_path)
    print(f"Total arquivos sem TAG: {len(untagged)}\n")

    # Match each file
    matches = []
    orphans = []

    for file_info in untagged:
        match = find_best_match(file_info["filename"])
        if match:
            matches.append({
                **file_info,
                **match
            })
        else:
            orphans.append(file_info)

    print(f"MATCHES ENCONTRADOS: {len(matches)}")
    print(f"ÓRFÃOS (sem match): {len(orphans)}\n")

    print("=== MATCHES DETALHADOS ===\n")
    for m in sorted(matches, key=lambda x: x["tag"]):
        print(f"[{m['tag']}] {m['filename']}")
        print(f"  → Planilha: {m['matched_to']} ({m['source']})")
        print(f"  → Score: {m['score']:.2%}")
        print(f"  → Path: {m['rel_path']}")
        print()

    print("\n=== ÓRFÃOS (ARQUIVOS SEM MATCH NA PLANILHA) ===\n")
    for o in orphans:
        print(f"  ✗ {o['rel_path']}")

    # Save results
    results = {
        "total_untagged": len(untagged),
        "total_matches": len(matches),
        "total_orphans": len(orphans),
        "matches": matches,
        "orphans": orphans
    }

    output_path = ".claude/mission-control/COMPLETE-TAG-MATCHING.json"
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)

    print(f"\n\nResultados salvos em: {output_path}")

    return results

if __name__ == "__main__":
    main()
