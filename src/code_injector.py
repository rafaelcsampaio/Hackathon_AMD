import os
import re
import pyperclip
from typing import Optional, Dict, Any

class CodeInjector:
    """
    Handles autonomous code delivery to the user's environment.
    Parses AI responses for action tags and securely injects or copies code.
    """
    
    def __init__(self, workspace_path: Optional[str] = None):
        self.workspace_path = workspace_path or os.getcwd()
        print(f"[CodeInjector] Initialized. Target workspace: {self.workspace_path}")

    def _extract_markdown_code(self, llm_response: str) -> Optional[str]:
        """
        Extracts the first valid markdown code block from the AI's response.
        Uses re.compile to ensure 'pattern' is a regex object, not a string.
        """
        backticks = chr(96) * 3
        pattern = re.compile(backticks + r"(?:\w+)?\s*\n([\s\S]+?)\n" + backticks)
        matches = pattern.findall(llm_response)
        
        if matches:
            return matches[0].strip()
        return None

    def _parse_ai_service_code(self, llm_response: str) -> Dict[str, Any]:
        """
        Parses the AI's response for specific service action tags.
        Example: [ACAO:INJETAR | main.py | 42]
        """
        inject_match = re.search(r'\[ACAO:INJETAR\s*\|\s*([\w.-]+)\s*\|\s*(\d+)\s*\]', llm_response)
        
        if inject_match:
            return {
                'action': 'inject',
                'target_file': inject_match.group(1),
                'target_line': int(inject_match.group(2))
            }
            
        if '[ACAO:COPIAR]' in llm_response:
            return {'action': 'copy'}
            
        # Default fallback action
        return {'action': 'copy'}

    def _copy_to_clipboard(self, code_content: str) -> str:
        """Silently copies the extracted code to the system clipboard."""
        try:
            pyperclip.copy(code_content)
            print("[CodeInjector] Code successfully copied to clipboard.")
            return "SUCCESS_COPIED"
        except Exception as e:
            print(f"[CodeInjector] Failed to access clipboard: {e}")
            return "ERROR"

    def _inject_into_file(self, file_name: str, line_number: int, code_content: str) -> str:
        """
        Injects the code directly into the specified file at the given line number.
        Recursively searches the workspace for the file.
        """
        caminhos_encontrados = []
        
        # Busca o arquivo em todas as pastas do projeto
        for root, dirs, files in os.walk(self.workspace_path):
            # Ignora pastas de sistema/ambiente virtual para ser rápido
            if 'venv' in root or '__pycache__' in root or '.git' in root:
                continue
            if file_name in files:
                caminhos_encontrados.append(os.path.join(root, file_name))
                
        # Se não achou em nenhuma pasta, avisa o main.py para fazer a pergunta por voz
        if not caminhos_encontrados:
            print(f"[CodeInjector] Warning: Target file '{file_name}' not found.")
            return "FILE_NOT_FOUND"

        # Pega o primeiro caminho válido encontrado
        file_path = caminhos_encontrados[0]

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                file_lines = f.readlines()

            # Pad with empty lines if the target line is beyond the file's current end
            while len(file_lines) < (line_number - 1):
                file_lines.append("\n")

            insert_index = max(0, line_number - 1)
            formatted_code = f"{code_content}\n"
            
            file_lines.insert(insert_index, formatted_code)

            with open(file_path, 'w', encoding='utf-8') as f:
                f.writelines(file_lines)
                
            print(f"[CodeInjector] Success: Ghost injection executed in {file_path} (Line {line_number}).")
            return "SUCCESS_INJECTED"
            
        except Exception as e:
            print(f"[CodeInjector] Critical Error during injection: {e}. Falling back to clipboard.")
            self._copy_to_clipboard(code_content)
            return "ERROR_FALLBACK"

    def execute_action(self, llm_response: str) -> str:
        """
        Main entry point. Extracts code and executes the decision made by the AI.
        Returns the status string so main.py knows what happened.
        """
        generated_code = self._extract_markdown_code(llm_response)
        
        if not generated_code:
            return "NO_ACTION"

        decision = self._parse_ai_service_code(llm_response)

        if decision['action'] == 'inject':
            return self._inject_into_file(
                file_name=decision['target_file'],
                line_number=decision['target_line'],
                code_content=generated_code
            )
        else:
            return self._copy_to_clipboard(generated_code)