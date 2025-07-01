
    from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc, func
from models.game import Game, GameSession, GameType, GameDifficulty, GameStatus
from models.user import User
from models.narrative_state import UserNarrativeState, UserArchetype
from config.database import get_db
from utils.lucien_voice import LucienVoice
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta
import random
import json
import math

class GameService:
    """Servicio para mini-juegos que Diana usa para evaluar personalidad"""
    
    def __init__(self):
        self.db = next(get_db())
        self.lucien = LucienVoice()
        
        # Configuración de juegos
        self.GAME_CONFIGS = self._load_game_configurations()
        
        # Multiplicadores de recompensa por dificultad
        self.DIFFICULTY_MULTIPLIERS = {
            GameDifficulty.EASY: 1.0,
            GameDifficulty.MEDIUM: 1.5,
            GameDifficulty.HARD: 2.0,
            GameDifficulty.EXPERT: 3.0
        }
        
        # Análisis de personalidad por juego
        self.PERSONALITY_INDICATORS = {
            GameType.RIDDLE: ['analytical', 'patient'],
            GameType.WORD_ASSOCIATION: ['creative', 'intuitive'],
            GameType.PATTERN_RECOGNITION: ['logical', 'detail_oriented'],
            GameType.MORAL_DILEMMA: ['ethical', 'thoughtful'],
            GameType.QUICK_CHOICE: ['decisive', 'spontaneous'],
            GameType.MEMORY_CHALLENGE: ['focused', 'persistent'],
            GameType.CREATIVITY_TEST: ['imaginative', 'artistic']
        }
    
    # ===== GESTIÓN DE SESIONES DE JUEGO =====
    
    def start_game_session(self, user_id: int, game_type: GameType, difficulty: GameDifficulty = GameDifficulty.MEDIUM) -> Dict[str, Any]:
        """Inicia nueva sesión de juego"""
        
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            return {"error": "Usuario no encontrado"}
        
        from services.user_service import UserService
        user_service = UserService()
        narrative_state = user_service.get_or_create_narrative_state(user_id)
        
        # Verificar si puede jugar (cooldown, límites diarios)
        play_validation = self._validate_game_session(user, game_type)
        if not play_validation['can_play']:
            return {"error": play_validation['message']}
        
        # Obtener configuración del juego
        game_config = self.GAME_CONFIGS.get(game_type.value, {})
        
        # Crear sesión de juego
        session = GameSession(
            user_id=user_id,
            game_type=game_type,
            difficulty=difficulty,
            started_at=datetime.utcnow(),
            game_data=self._generate_game_data(game_type, difficulty, narrative_state),
            metadata={
                'user_level': user.level,
                'narrative_level': narrative_state.current_level.value,
                'diana_interest': narrative_state.diana_interest_level,
                'user_archetype': narrative_state.primary_archetype.value if narrative_state.primary_archetype else None
            }
        )
        
        self.db.add(session)
        self.db.commit()
        self.db.refresh(session)
        
        # Generar introducción del juego por Lucien
        intro_message = self._generate_game_introduction(game_type, difficulty, narrative_state, user)
        
        return {
            "success": True,
            "session_id": session.id,
            "game_type": game_type.value,
            "difficulty": difficulty.value,
            "game_data": session.game_data,
            "intro_message": intro_message,
            "time_limit": game_config.get('time_limit_seconds'),
            "max_attempts": game_config.get('max_attempts', 1)
        }
    
    def submit_game_answer(self, session_id: int, user_answer: Any, time_taken: Optional[int] = None) -> Dict[str, Any]:
        """Procesa respuesta del usuario en el juego"""
        
        session = self.db.query(GameSession).filter(GameSession.id == session_id).first()
        if not session:
            return {"error": "Sesión de juego no encontrada"}
        
        if session.status != GameStatus.ACTIVE:
            return {"error": "Sesión de juego no está activa"}
        
        # Verificar tiempo límite
        if session.game_data.get('time_limit_seconds'):
            elapsed = (datetime.utcnow() - session.started_at).total_seconds()
            if elapsed > session.game_data['time_limit_seconds']:
                return self._handle_game_timeout(session)
        
        # Evaluar respuesta
        evaluation_result = self._evaluate_game_answer(session, user_answer, time_taken)
        
        # Actualizar sesión
        session.attempts_used += 1
        session.user_answers = session.user_answers or []
        session.user_answers.append({
            'answer': user_answer,
            'time_taken': time_taken,
            'timestamp': datetime.utcnow().isoformat(),
            'evaluation': evaluation_result
        })
        
        # Determinar si el juego terminó
        game_config = self.GAME_CONFIGS.get(session.game_type.value, {})
        max_attempts = game_config.get('max_attempts', 1)
        
        if evaluation_result['correct'] or session.attempts_used >= max_attempts:
            return self._complete_game_session(session, evaluation_result)
        else:
            # Continuar juego - dar feedback y siguiente oportunidad
            self.db.commit()
            return self._continue_game_session(session, evaluation_result)
    
    def get_game_leaderboard(self, game_type: Optional[GameType] = None, limit: int = 10) -> List[Dict[str, Any]]:
        """Obtiene leaderboard de juegos"""
        
        query = self.db.query(
            User.first_name,
            User.username,
            func.count(GameSession.id).label('games_played'),
            func.avg(GameSession.score).label('avg_score'),
            func.max(GameSession.score).label('best_score'),
            func.sum(GameSession.besitos_earned).label('total_besitos')
        ).join(
            GameSession, User.id == GameSession.user_id
        ).filter(
            GameSession.status == GameStatus.COMPLETED
        )
        
        if game_type:
            query = query.filter(GameSession.game_type == game_type)
        
        results = query.group_by(
            User.id
        ).order_by(
            desc('avg_score')
        ).limit(limit).all()
        
        leaderboard = []
        for i, (name, username, games, avg_score, best_score, total_besitos) in enumerate(results, 1):
            leaderboard.append({
                "position": i,
                "name": name,
                "username": username,
                "games_played": games,
                "average_score": round(avg_score, 1),
                "best_score": best_score,
                "total_besitos_earned": total_besitos or 0
            })
        
        return leaderboard
    
    def get_user_game_stats(self, user_id: int) -> Dict[str, Any]:
        """Obtiene estadísticas de juegos del usuario"""
        
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            return {"error": "Usuario no encontrado"}
        
        # Estadísticas generales
        total_games = self.db.query(GameSession).filter(
            GameSession.user_id == user_id
        ).count()
        
        completed_games = self.db.query(GameSession).filter(
            and_(
                GameSession.user_id == user_id,
                GameSession.status == GameStatus.COMPLETED
            )
        ).count()
        
        avg_score = self.db.query(func.avg(GameSession.score)).filter(
            and_(
                GameSession.user_id == user_id,
                GameSession.status == GameStatus.COMPLETED
            )
        ).scalar() or 0
        
        total_besitos = self.db.query(func.sum(GameSession.besitos_earned)).filter(
            GameSession.user_id == user_id
        ).scalar() or 0
        
        # Estadísticas por tipo de juego
        game_type_stats = {}
        for game_type in GameType:
            type_games = self.db.query(GameSession).filter(
                and_(
                    GameSession.user_id == user_id,
                    GameSession.game_type == game_type,
                    GameSession.status == GameStatus.COMPLETED
                )
            ).all()
            
            if type_games:
                game_type_stats[game_type.value] = {
                    "games_played": len(type_games),
                    "average_score": sum(g.score for g in type_games) / len(type_games),
                    "best_score": max(g.score for g in type_games)
                }
        
        # Análisis de personalidad basado en juegos
        personality_analysis = self._analyze_user_game_personality(user_id)
        
        return {
            "total_games": total_games,
            "completed_games": completed_games,
            "completion_rate": (completed_games / max(total_games, 1)) * 100,
            "average_score": round(avg_score, 1),
            "total_besitos_earned": total_besitos,
            "game_type_stats": game_type_stats,
            "personality_analysis": personality_analysis,
            "diana_commentary": self._generate_diana_game_commentary(personality_analysis, user)
        }
    
    # ===== GENERACIÓN DE JUEGOS =====
    
    def _generate_game_data(self, game_type: GameType, difficulty: GameDifficulty, narrative_state: UserNarrativeState) -> Dict[str, Any]:
        """Genera datos específicos del juego"""
        
        if game_type == GameType.RIDDLE:
            return self._generate_riddle_game(difficulty, narrative_state)
        
        elif game_type == GameType.WORD_ASSOCIATION:
            return self._generate_word_association_game(difficulty, narrative_state)
        
        elif game_type == GameType.PATTERN_RECOGNITION:
            return self._generate_pattern_game(difficulty)
        
        elif game_type == GameType.MORAL_DILEMMA:
            return self._generate_moral_dilemma_game(difficulty, narrative_state)
        
        elif game_type == GameType.QUICK_CHOICE:
            return self._generate_quick_choice_game(difficulty, narrative_state)
        
        elif game_type == GameType.MEMORY_CHALLENGE:
            return self._generate_memory_game(difficulty)
        
        elif game_type == GameType.CREATIVITY_TEST:
            return self._generate_creativity_game(difficulty, narrative_state)
        
        else:
            return {"error": "Tipo de juego no implementado"}
    
    def _generate_riddle_game(self, difficulty: GameDifficulty, narrative_state: UserNarrativeState) -> Dict[str, Any]:
        """Genera acertijo personalizado"""
        
        # Acertijos por dificultad con temática de Diana
        riddles_by_difficulty = {
            GameDifficulty.EASY: [
                {
                    "question": "Soy invisible pero todos me buscan, me gano con dedicación y se pierde con descuido. Diana me valora sobre todo. ¿Qué soy?",
                    "answer": "confianza",
                    "hints": ["Es algo emocional", "Se construye con tiempo", "Diana lo menciona frecuentemente"]
                },
                {
                    "question": "Tengo valor pero no precio, se otorgan por mérito y se acumulan con pasión. En las subastas de Diana soy poder. ¿Qué soy?",
                    "answer": "besitos",
                    "hints": ["Es la moneda del bot", "Se ganan con actividad", "Se usan en subastas"]
                }
            ],
            GameDifficulty.MEDIUM: [
                {
                    "question": "Soy un espacio íntimo donde pocos entran, mi acceso se gana con devoción y mi contenido es para quienes Diana considera especiales. ¿Qué soy?",
                    "answer": "divan",
                    "hints": ["Es un lugar exclusivo", "Requiere confianza de Diana", "No todos pueden acceder"]
                }
            ],
            GameDifficulty.HARD: [
                {
                    "question": "Observo, analizo y determino. Mi juicio define tu camino y mi comprensión te categoriza. Diana confía en mi evaluación para conocerte. ¿Quién soy?",
                    "answer": "lucien",
                    "hints": ["Es una persona del bot", "Hace análisis", "Es el mayordomo"]
                }
            ]
        }
        
        riddles = riddles_by_difficulty.get(difficulty, riddles_by_difficulty[GameDifficulty.EASY])
        selected_riddle = random.choice(riddles)
        
        # Personalizar según nivel narrativo
        if narrative_state.current_level.value in ['level_4_divan_entry', 'level_5_divan_deep', 'level_6_divan_supreme']:
            # Agregar contexto íntimo para usuarios del Diván
            selected_riddle['context'] = "Diana susurra este acertijo solo a quienes han ganado su confianza íntima..."
        
        return {
            "game_type": "riddle",
            "riddle": selected_riddle,
            "time_limit_seconds": 300,  # 5 minutos
            "hints_available": len(selected_riddle["hints"]),
            "scoring": {
                "correct_first_try": 100,
                "correct_with_hints": 60,
                "time_bonus_threshold": 120  # Bonus si resuelve en 2 minutos
            }
        }
    
    def _generate_word_association_game(self, difficulty: GameDifficulty, narrative_state: UserNarrativeState) -> Dict[str, Any]:
        """Genera juego de asociación de palabras"""
        
        # Palabras semilla relacionadas con Diana y el contexto narrativo
        seed_words_by_theme = {
            "seduction": ["mirada", "susurro", "proximidad", "tentación"],
            "power": ["control", "dominio", "autoridad", "influencia"],
            "intimacy": ["confianza", "secreto", "vulnerabilidad", "conexión"],
            "luxury": ["elegancia", "exclusividad", "refinamiento", "distinción"]
        }
        
        # Seleccionar tema basado en nivel narrativo
        if narrative_state.has_divan_access:
            theme = random.choice(["intimacy", "luxury"])
        else:
            theme = random.choice(["seduction", "power"])
        
        seed_word = random.choice(seed_words_by_theme[theme])
        
        return {
            "game_type": "word_association",
            "seed_word": seed_word,
            "theme": theme,
            "target_words": 5 if difficulty == GameDifficulty.EASY else 8,
            "time_limit_seconds": 180,
            "scoring": {
                "relevant_word": 15,
                "creative_word": 25,
                "theme_bonus": 10
            }
        }
    
    def _generate_pattern_game(self, difficulty: GameDifficulty) -> Dict[str, Any]:
        """Genera juego de reconocimiento de patrones"""
        
        pattern_length = {
            GameDifficulty.EASY: 4,
            GameDifficulty.MEDIUM: 6,
            GameDifficulty.HARD: 8,
            GameDifficulty.EXPERT: 10
        }
        
        length = pattern_length.get(difficulty, 4)
        
        # Generar secuencia de números o símbolos
        if difficulty in [GameDifficulty.EASY, GameDifficulty.MEDIUM]:
            # Secuencia numérica
            base = random.randint(1, 5)
            increment = random.randint(2, 4)
            sequence = [base + (i * increment) for i in range(length)]
        else:
            # Secuencia más compleja
            sequence = self._generate_complex_pattern(length)
        
        # Remover último elemento para que el usuario lo complete
        complete_sequence = sequence.copy()
        incomplete_sequence = sequence[:-1]
        missing_element = sequence[-1]
        
        return {
            "game_type": "pattern_recognition",
            "sequence": incomplete_sequence,
            "correct_answer": missing_element,
            "time_limit_seconds": 120,
            "difficulty_level": difficulty.value,
            "scoring": {
                "correct_answer": 100,
                "time_bonus_threshold": 60
            }
        }
    
    def _generate_moral_dilemma_game(self, difficulty: GameDifficulty, narrative_state: UserNarrativeState) -> Dict[str, Any]:
        """Genera dilema moral contextualizado"""
        
        # Dilemas morales en el contexto de Diana
        dilemmas = [
            {
                "situation": "Diana te ofrece contenido exclusivo, pero te pide que no lo compartas con nadie más, ni siquiera mencionar que lo tienes. ¿Qué haces?",
                "choices": [
                    {"text": "Acepto y mantengo el secreto completamente", "values": ["loyalty", "discretion"]},
                    {"text": "Acepto pero podría comentarlo vagamente", "values": ["honesty", "social"]},
                    {"text": "Declino la oferta para evitar compromisos", "values": ["independence", "caution"]},
                    {"text": "Acepto pero establecería mis propios términos", "values": ["assertiveness", "autonomy"]}
                ]
            },
            {
                "situation": "Descubres que otro usuario está haciendo trampa en las subastas. Diana no se ha dado cuenta. ¿Qué haces?",
                "choices": [
                    {"text": "Informo inmediatamente a Diana", "values": ["honesty", "justice"]},
                    {"text": "Confronto directamente al usuario", "values": ["directness", "courage"]},
                    {"text": "No me involucro, no es mi problema", "values": ["neutrality", "caution"]},
                    {"text": "Busco más evidencia antes de actuar", "values": ["analytical", "prudence"]}
                ]
            }
        ]
        
        selected_dilemma = random.choice(dilemmas)
        
        return {
            "game_type": "moral_dilemma",
            "dilemma": selected_dilemma,
            "time_limit_seconds": 300,
            "allows_explanation": True,
            "scoring": {
                "choice_made": 50,
                "explanation_bonus": 30,
                "consistency_bonus": 20
            }
        }
    
    def _generate_quick_choice_game(self, difficulty: GameDifficulty, narrative_state: UserNarrativeState) -> Dict[str, Any]:
        """Genera juego de elección rápida"""
        
        questions_count = {
            GameDifficulty.EASY: 5,
            GameDifficulty.MEDIUM: 8,
            GameDifficulty.HARD: 12
        }
        
        count = questions_count.get(difficulty, 5)
        
        # Preguntas rápidas sobre preferencias
        question_pool = [
            {"question": "¿Prefieres?", "option_a": "Una noche íntima", "option_b": "Una aventura emocionante"},
            {"question": "Diana te mira fijamente. ¿Tu reacción?", "option_a": "Sostengo la mirada", "option_b": "Miro hacia otro lado"},
            {"question": "¿Qué te atrae más?", "option_a": "El misterio", "option_b": "La claridad"},
            {"question": "En una subasta, ¿prefieres?", "option_a": "Pujar al final", "option_b": "Pujar desde el inicio"},
            {"question": "¿Cómo te gusta recibir atención?", "option_a": "Gradualmente", "option_b": "Intensamente"},
        ]
        
        selected_questions = random.sample(question_pool, min(count, len(question_pool)))
        
        return {
            "game_type": "quick_choice",
            "questions": selected_questions,
            "time_per_question": 10,  # 10 segundos por pregunta
            "total_time_limit": count * 10,
            "scoring": {
                "quick_answer": 10,
                "consistency_bonus": 20
            }
        }
    
    def _generate_memory_game(self, difficulty: GameDifficulty) -> Dict[str, Any]:
        """Genera desafío de memoria"""
        
        sequence_length = {
            GameDifficulty.EASY: 4,
            GameDifficulty.MEDIUM: 6,
            GameDifficulty.HARD: 8,
            GameDifficulty.EXPERT: 10
        }

Perfecto adelante
   