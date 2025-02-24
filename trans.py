import riva.client
import riva.client.audio_io

class RivaArguments:
    def __init__(
            self,
            max_alternatives: bool = False,
            profanity_filter: bool = True,
            word_time_offsets: bool = False
    ):
        default_device_info = riva.client.audio_io.get_default_input_device_info()
        self.input_device: int = None if default_device_info is None else default_device_info['index']
        self.list_devices: bool = False

        self.word_time_offsets: bool = False if word_time_offsets else None
        self.max_alternatives: int = 1 if max_alternatives else None
        self.profanity_filter: bool = False if profanity_filter else None

        self.server: str = "localhost:50051"
        self.ssl_cert: str = None
        self.use_ssl: bool = False
        self.metadata: list = []
        self.sample_rate_hz: int = 16000
        self.file_streaming_chunk: int = 1600
        self.target_language_code: str = "fr-FR"
        self.automatic_punctuation: bool = False
        self.no_verbatim_transcripts: bool = False
        self.asr_language_code: str = "en-US"
        self.model_name: str = ""
        self.boosted_lm_words: list = []
        self.boosted_lm_score: float = 4.0
        self.speaker_diarization: bool = False
        self.diarization_max_speakers: int = 3
        self.start_history: int = -1
        self.start_threshold: float = -1.0
        self.stop_history: int = -1
        self.stop_threshold: float = -1.0
        self.stop_history_eou: int = -1
        self.stop_threshold_eou: float = -1.0
        self.custom_configuration: str = ""

    # Setters for each property
    def set_input_device(self, device_index: int):
        """Set input audio device index."""
        self.input_device = device_index

    def set_list_devices(self, list_devices: bool):
        """Enable or disable listing audio devices."""
        self.list_devices = list_devices

    def set_word_time_offsets(self, enabled: bool):
        """Enable or disable word time offsets."""
        self.word_time_offsets = enabled

    def set_max_alternatives(self, max_alternatives: int):
        """Set maximum number of alternative transcriptions."""
        if max_alternatives >= 1:
            self.max_alternatives = max_alternatives
        else:
            raise ValueError("max_alternatives must be at least 1.")

    def set_profanity_filter(self, enabled: bool):
        """Enable or disable the profanity filter."""
        self.profanity_filter = enabled

    def set_server(self, server: str):
        """Set the gRPC server address."""
        self.server = server

    def set_ssl_cert(self, cert_path: str):
        """Set SSL certificate file path."""
        self.ssl_cert = cert_path

    def set_use_ssl(self, use_ssl: bool):
        """Enable or disable SSL encryption."""
        self.use_ssl = use_ssl

    def set_metadata(self, metadata: list):
        """Set HTTP metadata headers."""
        self.metadata = metadata

    def set_sample_rate_hz(self, sample_rate: int):
        """Set audio sample rate (frames per second)."""
        if sample_rate > 0:
            self.sample_rate_hz = sample_rate
        else:
            raise ValueError("sample_rate_hz must be greater than 0.")

    def set_file_streaming_chunk(self, chunk_size: int):
        """Set the maximum audio chunk size."""
        if chunk_size > 0:
            self.file_streaming_chunk = chunk_size
        else:
            raise ValueError("file_streaming_chunk must be greater than 0.")

    def set_target_language_code(self, code: str):
        """Set the target language code."""
        self.target_language_code = code

    def set_automatic_punctuation(self, enabled: bool):
        """Enable or disable automatic punctuation."""
        self.automatic_punctuation = enabled

    def set_no_verbatim_transcripts(self, enabled: bool):
        """Enable or disable text normalization."""
        self.no_verbatim_transcripts = enabled

    def set_asr_language_code(self, code: str):
        """Set the model language code."""
        self.asr_language_code = code

    def set_model_name(self, name: str):
        """Set the ASR model name."""
        self.model_name = name

    def set_boosted_lm_words(self, words: list):
        """Set words to boost for recognition."""
        self.boosted_lm_words = words

    def set_boosted_lm_score(self, score: float):
        """Set boost score for language model words."""
        if score >= 0:
            self.boosted_lm_score = score
        else:
            raise ValueError("boosted_lm_score must be non-negative.")

    def set_speaker_diarization(self, enabled: bool):
        """Enable or disable speaker diarization."""
        self.speaker_diarization = enabled

    def set_diarization_max_speakers(self, num_speakers: int):
        """Set the maximum number of speakers for diarization."""
        if num_speakers > 0:
            self.diarization_max_speakers = num_speakers
        else:
            raise ValueError("diarization_max_speakers must be greater than 0.")

    def set_start_history(self, history: int):
        """Set start of speech detection history in milliseconds."""
        self.start_history = history

    def set_start_threshold(self, threshold: float):
        """Set start of speech detection threshold."""
        self.start_threshold = threshold

    def set_stop_history(self, history: int):
        """Set stop of speech detection history in milliseconds."""
        self.stop_history = history

    def set_stop_threshold(self, threshold: float):
        """Set stop of speech detection threshold."""
        self.stop_threshold = threshold

    def set_stop_history_eou(self, history: int):
        """Set end of utterance history in milliseconds."""
        self.stop_history_eou = history

    def set_stop_threshold_eou(self, threshold: float):
        """Set end of utterance blank frame threshold."""
        self.stop_threshold_eou = threshold

    def set_custom_configuration(self, config: str):
        """Set custom ASR configurations."""
        self.custom_configuration = config

def trans(args: RivaArguments, audio_chunk_iterator) -> None:
    args = RivaArguments(profanity_filter = True)
    if args.list_devices:
        riva.client.audio_io.list_input_devices()
        return
    auth = riva.client.Auth(args.ssl_cert, args.use_ssl, args.server, args.metadata)
    # asr_service = riva.client.ASRService(auth)
    nmt_client = riva.client.NeuralMachineTranslationClient(auth)
    
    config = riva.client.StreamingRecognitionConfig(
        config=riva.client.RecognitionConfig(
            encoding=riva.client.AudioEncoding.LINEAR_PCM,
            language_code=args.asr_language_code,
            model=args.model_name,
            max_alternatives=1,
            profanity_filter=args.profanity_filter,
            enable_automatic_punctuation=args.automatic_punctuation,
            verbatim_transcripts=not args.no_verbatim_transcripts,
            sample_rate_hertz=args.sample_rate_hz,
            audio_channel_count=1,
        ),
        interim_results=True,
    )
    
    riva.client.add_word_boosting_to_config(config, args.boosted_lm_words, args.boosted_lm_score)
    riva.client.add_endpoint_parameters_to_config(
        config,
        args.start_history,
        args.start_threshold,
        args.stop_history,
        args.stop_history_eou,
        args.stop_threshold,
        args.stop_threshold_eou
    )
    riva.client.add_custom_configuration_to_config(
        config,
        args.custom_configuration
    )

    config = riva.client.StreamingTranslateSpeechToTextConfig(
        asr_config=config,
        translation_config=riva.client.TranslationConfig(
            source_language_code=args.asr_language_code,
            target_language_code=args.target_language_code,
        ),
    )

    riva.client.print_streaming(
        responses=nmt_client.streaming_s2t_response_generator(
            audio_chunks=audio_chunk_iterator,
            streaming_config=config,
        ),
        show_intermediate=True,
    )