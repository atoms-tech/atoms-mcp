"""
Epic-based PM View

Shows user stories grouped by epics with pass/fail status.
"""

from typing import Dict, List
from .user_story_mapping import UserStoryMapper
from .matrix_views import MatrixCollector


class EpicView:
    """Renders epic-based user story view for PMs."""
    
    def __init__(self, collector: MatrixCollector):
        self.collector = collector
        self.mapper = UserStoryMapper()
    
    def is_story_passing(self, story: str) -> tuple[bool, str]:
        """
        Check if all tests for a user story are passing.
        
        Returns:
            (is_passing, reason) tuple where reason explains status
        """
        patterns = self.mapper.get_test_patterns_for_story(story)
        if not patterns:
            return False, "No tests mapped"
        
        passing_tests = []
        failing_tests = []
        skipped_tests = []
        
        # Check each test pattern - look for ANY substring match
        for pattern in patterns:
            for layer_results in self.collector.results.values():
                for mode_results in layer_results.values():
                    for result in mode_results:
                        # More flexible matching - check if pattern appears anywhere in test name
                        if any(p.lower() in result.name.lower() for p in pattern.split("::")):
                            if result.outcome == "passed":
                                passing_tests.append(result.name)
                            elif result.outcome == "failed":
                                failing_tests.append(result.name)
                            elif result.outcome == "skipped":
                                skipped_tests.append(result.name)
        
        # Determine status and reason
        total_tests = len(passing_tests) + len(failing_tests) + len(skipped_tests)
        
        if total_tests == 0:
            # No tests found matching these patterns
            return False, "No matching tests found"
        
        if passing_tests:
            if failing_tests:
                return True, f"{len(passing_tests)} passing, {len(failing_tests)} failing"
            elif skipped_tests:
                return True, f"{len(passing_tests)} passing, {len(skipped_tests)} skipped"
            else:
                return True, ""  # Clean success, no reason needed
        elif failing_tests:
            return False, f"{len(failing_tests)} test(s) failing"
        elif skipped_tests:
            return False, f"{len(skipped_tests)} test(s) skipped"
        else:
            return False, "No matching tests found"
    
    def render(self) -> str:
        """Generate epic-based PM view ASCII art."""
        lines = []
        
        # Header
        lines.append("╔" + "═"*78 + "╗")
        lines.append("║" + "ATOMS MCP - EPIC VIEW (User Stories)".center(78) + "║")
        lines.append("╠" + "═"*78 + "╣")
        
        total_stories = 0
        total_complete = 0
        
        # Process each epic
        for epic in self.mapper.get_epics():
            stories = self.mapper.get_stories_for_epic(epic)
            
            if not stories:
                continue
            
            # Count completed stories in this epic
            complete_count = sum(1 for story in stories if self.is_story_passing(story)[0])
            total_count = len(stories)
            
            total_stories += total_count
            total_complete += complete_count
            
            # Epic status
            completion_pct = complete_count / total_count if total_count else 0
            if completion_pct == 1.0:
                epic_status = "✓✓✓"
            elif completion_pct >= 0.7:
                epic_status = "✓✓○"
            elif completion_pct > 0:
                epic_status = "✓○○"
            else:
                epic_status = "○○○"
            
            # Epic header
            lines.append("║" + " "*78 + "║")
            epic_line = f"📦 {epic} ({complete_count}/{total_count}) {epic_status}"
            lines.append("║ " + epic_line + " "*(77 - len(epic_line)) + "║")
            lines.append("║" + "─"*78 + "║")
            
            # Show individual user stories with reasons
            for story in stories:
                is_passing, reason = self.is_story_passing(story)
                status = "✅" if is_passing else "❌"
                
                # Truncate story if too long
                max_story_len = 50
                if len(story) > max_story_len:
                    story_display = story[:max_story_len-3] + "..."
                else:
                    story_display = story
                
                # Add reason if not passing or if there are warnings
                if not is_passing or "skipped" in reason or "failing" in reason:
                    story_line = f"  {status} {story_display} ({reason})"
                else:
                    story_line = f"  {status} {story_display}"
                
                # Truncate full line if too long
                if len(story_line) > 76:
                    story_line = story_line[:73] + "..."
                
                lines.append("║ " + story_line + " "*(77 - len(story_line)) + "║")
        
        # Summary
        lines.append("╠" + "═"*78 + "╣")
        pct = int(total_complete / total_stories * 100) if total_stories else 0
        summary = f"Overall: {total_complete}/{total_stories} user stories complete ({pct}%)"
        lines.append("║ " + summary + " "*(77 - len(summary)) + "║")
        lines.append("╚" + "═"*78 + "╝")
        
        return "\n".join(lines)
    
    def render_compact(self) -> str:
        """Generate compact epic summary."""
        lines = []
        
        lines.append("╔" + "═"*78 + "╗")
        lines.append("║" + "ATOMS MCP - EPIC SUMMARY".center(78) + "║")
        lines.append("╠" + "═"*78 + "╣")
        lines.append("║ Epic                          │ Stories │ Complete │ Status      ║")
        lines.append("╠" + "─"*31 + "┼" + "─"*9 + "┼" + "─"*10 + "┼" + "─"*13 + "╣")
        
        total_stories = 0
        total_complete = 0
        
        for epic in self.mapper.get_epics():
            stories = self.mapper.get_stories_for_epic(epic)
            complete_count = sum(1 for story in stories if self.is_story_passing(story)[0])
            total_count = len(stories)
            
            total_stories += total_count
            total_complete += complete_count
            
            completion_pct = complete_count / total_count if total_count else 0
            if completion_pct == 1.0:
                status = "✓✓✓"
            elif completion_pct >= 0.7:
                status = "✓✓○"
            elif completion_pct > 0:
                status = "✓○○"
            else:
                status = "○○○"
            
            # Truncate epic name if needed
            epic_display = epic[:28] if len(epic) > 28 else epic
            
            line = f"║ {epic_display:<29} │ {total_count:>7} │ {complete_count:>8} │ {status:>11} ║"
            lines.append(line)
        
        # Summary
        lines.append("╠" + "─"*78 + "╣")
        pct = int(total_complete / total_stories * 100) if total_stories else 0
        summary = f"Total: {total_complete}/{total_stories} user stories complete ({pct}%)"
        lines.append("║ " + summary + " "*(77 - len(summary)) + "║")
        lines.append("╚" + "═"*78 + "╝")
        
        return "\n".join(lines)
