#!/usr/bin/env nextflow
nextflow.enable.dsl=2

def stageIdx(stage) { ['crop', 'segmentation', 'features', 'prediction'].indexOf(stage as String) }

def boolParam(value) {
    if( value == null ) {
        return false
    }
    if( value instanceof Boolean ) {
        return value
    }
    if( value instanceof Number ) {
        return value != 0
    }
    return value.toString().trim().toLowerCase() in ['true', '1', 'yes', 'y', 'on']
}

def validateParams(activeFrom, activeTo) {
    if( !['crop', 'segmentation', 'features', 'prediction'].contains(activeFrom as String) ) {
        if( params.stage != null ) {
            error "Invalid --stage '${activeFrom}'. Allowed: crop, segmentation, features, prediction"
        }
        error "Invalid --from_stage '${activeFrom}'. Allowed: crop, segmentation, features, prediction"
    }
    if( !['crop', 'segmentation', 'features', 'prediction'].contains(activeTo as String) ) {
        if( params.stage != null ) {
            error "Invalid --stage '${activeTo}'. Allowed: crop, segmentation, features, prediction"
        }
        error "Invalid --to_stage '${activeTo}'. Allowed: crop, segmentation, features, prediction"
    }
    if( stageIdx(activeFrom) > stageIdx(activeTo) ) {
        error "from_stage '${activeFrom}' must not come after to_stage '${activeTo}'"
    }

    def fromIdx = stageIdx(activeFrom)
    def toIdx   = stageIdx(activeTo)

    // Input validation per entry stage
    if( activeFrom == 'crop' ) {
        if( !params.slide_root ) {
            error "For --stage/--from_stage crop, --slide_root is required"
        }
    }
    else if( activeFrom == 'segmentation' ) {
        if( !params.crop_root ) {
            error "For --stage/--from_stage segmentation, --crop_root is required"
        }
    }
    else if( activeFrom == 'features' ) {
        if( !['roots', 'samplesheet'].contains(params.input_mode as String) ) {
            error "Invalid --input_mode '${params.input_mode}'. Expected: roots | samplesheet"
        }
        if( params.input_mode == 'roots' ) {
            if( !params.image_root || !params.mat_root ) {
                error "For input_mode=roots, both --image_root and --mat_root are required"
            }
            if( params.samplesheet ) {
                error "For input_mode=roots, do not set --samplesheet"
            }
        }
        if( params.input_mode == 'samplesheet' ) {
            if( !params.samplesheet ) {
                error "For input_mode=samplesheet, --samplesheet is required"
            }
            if( params.image_root || params.mat_root ) {
                error "For input_mode=samplesheet, do not set --image_root or --mat_root"
            }
        }
    }
    else if( activeFrom == 'prediction' ) {
        if( !params.features_root ) {
            error "For --stage/--from_stage prediction, --features_root is required"
        }
    }

    if( !boolParam(params.fail_on_missing_model_features) ) {
        error "This pipeline currently requires --fail_on_missing_model_features=true"
    }
    if( !['legacy', 'dual', 'v2'].contains(params.feature_schema as String) ) {
        error "Invalid --feature_schema '${params.feature_schema}'. Expected: legacy | dual | v2"
    }

    // Container validation for active stages.
    if( fromIdx <= stageIdx('segmentation') && toIdx >= stageIdx('segmentation') ) {
        if( params.seg_container == null || params.seg_container == 'docker.io/<owner>/nucxplore-seg:<tag>' ) {
            error "Segmentation stage requires --seg_container to be set to a valid image (current: ${params.seg_container})"
        }
    }
    if( fromIdx <= stageIdx('prediction') && toIdx >= stageIdx('prediction') ) {
        if( params.container == null || params.container == 'docker.io/<owner>/nucxplore-cell-type-prediction:<tag>' ) {
            error "Prediction stage requires --container to be set to a valid image (current: ${params.container})"
        }
    }
}

process CROP_AND_FILTER {
    tag "crop-${slide_path.baseName}"
    publishDir "${params.outdir}", mode: 'copy', pattern: 'crops', enabled: params.publish_crops.toString().toBoolean()
    publishDir "${params.outdir}/logs", mode: 'copy', pattern: 'crop_manifest.json'
    publishDir "${params.outdir}/logs", mode: 'copy', pattern: 'crop.log'

    input:
    path slide_path

    output:
    path 'crops', emit: cropped_dir
    path 'crop_manifest.json', emit: manifest
    path 'crop.log', emit: log

    script:
    def dropPartialFlag = boolParam(params.drop_partial_tiles) ? '' : '--no-drop-partial-tiles'
    """
    mkdir -p crops
    conda run -n nucxplore-local crop_and_filter.py \
      --slide-path ${slide_path} \
      --output-root crops \
      --tile-size ${params.tile_size} \
      --mean-threshold ${params.mean_threshold} \
      --std-threshold ${params.std_threshold} \
      ${dropPartialFlag} \
      --slide-exts '${params.slide_exts}' \
      --output-manifest crop_manifest.json \
      --log-file crop.log
    """

    stub:
    """
    mkdir -p crops/${slide_path.baseName}
    printf '{}' > crops/${slide_path.baseName}/stub_tile.png
    printf '{"stub":true,"summary":{"total_slides":1,"kept_tiles":1}}\n' > crop_manifest.json
    : > crop.log
    """
}

process NUCXPLORE_SEG {
    tag "seg-${crop_root}"
    label 'segmentation'
    container params.seg_container
    maxForks 1
    accelerator request: (params.seg_device == 'cuda' ? params.seg_n_devices as Integer : 0), type: 'gpu'
    publishDir "${params.outdir}", mode: 'copy', pattern: 'segmentation_mats', enabled: params.publish_segmentation.toString().toBoolean()
    publishDir "${params.outdir}/logs", mode: 'copy', pattern: 'segmentation_manifest.json'
    publishDir "${params.outdir}/logs", mode: 'copy', pattern: 'segment.log'

    input:
    path crop_root

    output:
    path 'segmentation_mats', emit: mats_dir
    path 'segmentation_manifest.json', emit: manifest
    path 'segment.log', emit: log

    script:
    """
    exec nucxplore_seg_to_mat.py \
      --crop-root ${crop_root} \
      --output-root segmentation_mats \
      --checkpoint ${params.seg_checkpoint} \
      --device ${params.seg_device} \
      --n-devices ${params.seg_n_devices} \
      --batch-size ${params.seg_batch_size} \
      --patch-size ${params.seg_patch_size} \
      --stride ${params.seg_stride} \
      --padding ${params.seg_padding} \
      --output-manifest segmentation_manifest.json \
      --log-file segment.log
    """

    stub:
    """
    mkdir -p segmentation_mats/sample_slide
    printf '{"stub":true,"summary":{"total_samples":1,"successful":1}}\n' > segmentation_manifest.json
    : > segment.log
    """
}

process PREPARE_SAMPLESHEET {
    tag "stage-samplesheet"
    publishDir "${params.outdir}/logs", mode: 'copy', pattern: 'prepare_inputs_manifest.json'

    input:
    path samplesheet

    output:
    path 'prepared/images', emit: image_root
    path 'prepared/mats', emit: mat_root
    path 'prepare_inputs_manifest.json', emit: manifest

    script:
    """
    conda run -n nucxplore-local python ${projectDir}/bin/samplesheet_to_pairs.py \
      --samplesheet ${samplesheet} \
      --images-out prepared/images \
      --mats-out prepared/mats \
      --manifest prepare_inputs_manifest.json
    """

    stub:
    """
    mkdir -p prepared/images prepared/mats
    printf '{"sample_count":0,"stub":true}\n' > prepare_inputs_manifest.json
    """
}

process DISCOVER_PAIRS {
    tag "discover-pairs"
    conda 'nucxplore-local'

    input:
    tuple path(crop_root), path(mat_root)

    output:
    path 'pairs.csv', emit: pairs_csv

    script:
    """
    conda run -n nucxplore-local python ${projectDir}/bin/discover_pairs.py \\
      --crop-root ${crop_root} \\
      --mat-root ${mat_root} \\
      --output pairs.csv
    """

    stub:
    """
    printf 'tile_name,image_path,mat_path\\nstub,/stub.png,/stub.mat\\n' > pairs.csv
    """
}

process EXTRACT_FEATURES_PER_TILE {
    conda 'nucxplore-local'
    tag "feat-${tile_name}"
    publishDir "${params.outdir}/features", mode: 'copy'

    input:
    tuple val(tile_name), path(image_png), path(mat_file)

    output:
    path "${tile_name}.csv",   emit: feature_csv
    path "${tile_name}.csv.schema.json", emit: feature_schema_metadata
    path "${tile_name}_nuclei", emit: nuclei_dir, optional: true

    script:
    def matKeyArg = params.mat_key ? "--mat-key ${params.mat_key}" : ''
    def cropsFlag = boolParam(params.save_crops) ? '--save-crops' : ''
    def useGpuFlag = boolParam(params.use_gpu) ? '--use-gpu' : ''
    def featureSchemaArg = "--feature-schema ${params.feature_schema}"
    def cropsDirArg = boolParam(params.save_crops) ? "--crop-output-dir ${tile_name}_nuclei" : ''
    """
    conda run -n nucxplore-local python ${projectDir}/bin/extract_single_tile.py \\
      --image-path ${image_png} \\
      --mat-path ${mat_file} \\
      --output-csv ${tile_name}.csv \\
      --inst-type-key '${params.inst_type_key}' \\
      --padding ${params.padding} \\
      ${featureSchemaArg} \\
      ${matKeyArg} \\
      ${cropsFlag} \\
      ${useGpuFlag} \\
      ${cropsDirArg}
    """

    stub:
    """
    printf 'nucleus_id,area\\n1,10.0\\n' > ${tile_name}.csv
    printf '{"feature_schema":"${params.feature_schema}","algorithm_revision":"v3.0","stain_normalization":true}\\n' > ${tile_name}.csv.schema.json
    """
}

process PREDICT_CELL_TILES {
    tag "predict-tiles"
    container params.container
    maxForks 1
    publishDir "${params.outdir}/predictions", mode: 'copy'
    publishDir "${params.outdir}/logs", mode: 'copy', pattern: 'manifest.json'
    publishDir "${params.outdir}/logs", mode: 'copy', pattern: 'manifest.csv'
    publishDir "${params.outdir}/logs", mode: 'copy', pattern: 'predict.log'

    input:
    path feature_inputs, stageAs: 'feature_inputs/*'

    output:
    path 'predictions',      emit: predictions_dir
    path 'predictions/**',    emit: prediction_files, optional: true
    path 'manifest.json',    emit: manifest_json
    path 'manifest.csv',     emit: manifest_csv
    path 'predict.log',      emit: predict_log

    script:
    """
    cell_type_predict.py \\
      --input-features feature_inputs \\
      --output-dir predictions \\
      --model ${params.model_path} \\
      --encoder ${params.encoder_path} \\
      --workers ${params.workers} \\
      --manifest-json manifest.json \\
      --manifest-csv manifest.csv \\
      > predict.log 2>&1
    """

    stub:
    """
    mkdir -p predictions
    printf 'nucleus_id,Predicted_Label,Confidence_Score\\n1,StubCell,1.0\\n' > predictions/stub_predictions.csv
    printf '{"ok_files":1,"failed_files":0,"stub":true}\\n' > manifest.json
    printf 'status,input_csv,output_csv,rows,error\\nok,stub_features.csv,stub_predictions.csv,1,\\n' > manifest.csv
    : > predict.log
    """
}

workflow {
    // Resolve stage range: --stage overrides from_stage/to_stage
    fromStage = params.stage ?: params.from_stage
    toStage   = params.stage ?: params.to_stage

    validateParams(fromStage, toStage)
    fromIdx = stageIdx(fromStage)
    toIdx   = stageIdx(toStage)

    // ==================== crop (idx 0) ====================
    if( fromIdx == 0 ) {
        def slideExtList = params.slide_exts.split(',').collect { it.trim().toLowerCase() }
        slideCh = Channel
            .fromPath("${params.slide_root}/*")
            .filter { f -> slideExtList.any { ext -> f.name.toLowerCase().endsWith(ext) } }
        cropped_result = CROP_AND_FILTER(slideCh)
        if( toIdx == 0 ) { return }
    }

    // ==================== segmentation (idx 1) ====================
    if( fromIdx <= 1 && toIdx >= 1 ) {
        if( fromIdx == 1 ) {
            cropCh = Channel.value(file(params.crop_root, checkIfExists: true))
            if( toIdx >= 2 ) {
                cropCh_for_features = Channel.value(file(params.crop_root, checkIfExists: true))
            }
        }
        else {
            // Collect per-slide crop dirs. With a single slide, dirs[0] is the
            // work-dir crops/ path containing one slide subdirectory.
            cropCh = cropped_result.cropped_dir
                .collect()
                .map { dirs -> dirs[0] }
            if( toIdx >= 2 ) {
                cropCh_for_features = cropped_result.cropped_dir
                    .collect()
                    .map { dirs -> dirs[0] }
            }
        }
        seg_result = NUCXPLORE_SEG(cropCh)
        if( toIdx == 1 ) { return }
    }

    // ==================== features (idx 2) ====================
    if( fromIdx <= 2 && toIdx >= 2 ) {
        if( fromIdx == 2 ) {
            // Standalone features entry.
            if( params.input_mode == 'samplesheet' ) {
                staged = PREPARE_SAMPLESHEET(file(params.samplesheet, checkIfExists: true))
                imageRootCh = staged.image_root
                matRootCh = staged.mat_root
            }
            else {
                imageRootCh = Channel.value(file(params.image_root, checkIfExists: true))
                matRootCh = Channel.value(file(params.mat_root, checkIfExists: true))
            }
        }
        else if( fromIdx == 1 ) {
            imageRootCh = cropCh_for_features
            matRootCh = seg_result.mats_dir
        }
        else {
            imageRootCh = cropCh_for_features
            matRootCh = seg_result.mats_dir
        }
        // Discover per-tile (tile_name, png, mat) pairs and extract per tile
        pairCh = DISCOVER_PAIRS(imageRootCh.combine(matRootCh)).pairs_csv
        tileCh = pairCh
            .splitCsv(header: true, sep: ',')
            .map { row -> tuple(row.tile_name, file(row.image_path), file(row.mat_path)) }
        extracted = EXTRACT_FEATURES_PER_TILE(tileCh)
        if( toIdx == 2 ) { return }
    }

    // ==================== prediction (idx 3) ====================
    if( fromIdx <= 3 && toIdx >= 3 ) {
        if( fromIdx == 3 ) {
            // Standalone prediction: batch-predict all CSVs in features_root
            predInputCh = Channel.value(file(params.features_root, checkIfExists: true))
            PREDICT_CELL_TILES(predInputCh)
        }
        else {
            // From features: batch-predict all per-tile CSVs
            PREDICT_CELL_TILES(extracted.feature_csv.collect())
        }
        if( toIdx == 3 ) { return }
    }
}
