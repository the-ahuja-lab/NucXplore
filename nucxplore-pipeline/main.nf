#!/usr/bin/env nextflow
nextflow.enable.dsl=2

def stageIdx(stage) { ['crop', 'segmentation', 'features', 'prediction'].indexOf(stage as String) }

def validateParams() {
    if( !['crop', 'segmentation', 'features', 'prediction'].contains(params.from_stage as String) ) {
        error "Invalid --from_stage '${params.from_stage}'. Allowed: crop, segmentation, features, prediction"
    }
    if( !['crop', 'segmentation', 'features', 'prediction'].contains(params.to_stage as String) ) {
        error "Invalid --to_stage '${params.to_stage}'. Allowed: crop, segmentation, features, prediction"
    }
    if( stageIdx(params.from_stage) > stageIdx(params.to_stage) ) {
        error "--from_stage '${params.from_stage}' must not come after --to_stage '${params.to_stage}'"
    }

    def fromIdx = stageIdx(params.from_stage)
    def toIdx   = stageIdx(params.to_stage)

    // Input validation per entry stage
    if( params.from_stage == 'crop' ) {
        if( !params.slide_root ) {
            error "For --from_stage crop, --slide_root is required"
        }
    }
    else if( params.from_stage == 'segmentation' ) {
        if( !params.crop_root ) {
            error "For --from_stage segmentation, --crop_root is required"
        }
    }
    else if( params.from_stage == 'features' ) {
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
    else if( params.from_stage == 'prediction' ) {
        if( !params.features_root ) {
            error "For --from_stage prediction, --features_root is required"
        }
    }

    if( !(params.fail_on_missing_model_features in [true, 'true', 'True', 1, '1']) ) {
        error "This pipeline currently requires --fail_on_missing_model_features=true"
    }

    // Container validation for active stages (index-based so lexicographic ordering
    // doesn't corrupt the stage-order comparison).
    if( fromIdx <= stageIdx('crop') && toIdx >= stageIdx('crop') ) {
        if( params.crop_filter_container == null || params.crop_filter_container == 'docker.io/<owner>/nucxplore-crop-filter:<tag>' ) {
            error "Crop stage requires --crop_filter_container to be set to a valid image (current: ${params.crop_filter_container})"
        }
    }
    if( fromIdx <= stageIdx('segmentation') && toIdx >= stageIdx('segmentation') ) {
        if( params.seg_container == null || params.seg_container == 'docker.io/<owner>/nucxplore-rgci-seg:<tag>' ) {
            error "Segmentation stage requires --seg_container to be set to a valid image (current: ${params.seg_container})"
        }
    }
    if( (fromIdx <= stageIdx('features') && toIdx >= stageIdx('features')) ||
        (fromIdx <= stageIdx('prediction') && toIdx >= stageIdx('prediction')) ) {
        if( params.container == null || params.container == 'docker.io/<owner>/nucxplore-cell-type-prediction:<tag>' ) {
            error "Features/prediction stages require --container to be set to a valid image (current: ${params.container})"
        }
    }
}

process CROP_AND_FILTER {
    tag "crop-${slide_root}"
    label 'crop'
    container params.crop_filter_container
    publishDir "${params.outdir}/crops", mode: 'copy', pattern: 'cropped/**', enabled: params.publish_crops
    publishDir "${params.outdir}/logs", mode: 'copy', pattern: 'crop_manifest.json'
    publishDir "${params.outdir}/logs", mode: 'copy', pattern: 'crop.log'

    input:
    path slide_root

    output:
    path 'cropped', emit: cropped_dir
    path 'crop_manifest.json', emit: manifest
    path 'crop.log', emit: log

    script:
    def dropPartialFlag = params.drop_partial_tiles ? '' : '--no-drop-partial-tiles'
    def recursiveFlag = params.crop_recursive ? '--recursive' : ''
    """
    crop_and_filter.py \
      --slide-root ${slide_root} \
      --output-root cropped \
      --tile-size ${params.tile_size} \
      --mean-threshold ${params.mean_threshold} \
      --std-threshold ${params.std_threshold} \
      ${dropPartialFlag} \
      ${recursiveFlag} \
      --slide-exts '${params.slide_exts}' \
      --output-manifest crop_manifest.json \
      --log-file crop.log
    """

    stub:
    """
    mkdir -p cropped/sample_slide
    printf '{}' > cropped/sample_slide/patch_x-0_y-0.png
    printf '{"stub":true,"summary":{"total_slides":1,"kept_tiles":1}}\n' > crop_manifest.json
    : > crop.log
    """
}

process RGCI_SEG {
    tag "seg-${crop_root}"
    label 'segmentation'
    container params.seg_container
    publishDir "${params.outdir}/segmentation_mats", mode: 'copy', pattern: 'segmentation_mats/**', enabled: params.publish_segmentation
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
    rgci_seg_to_mat.py \
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
    python ${projectDir}/bin/samplesheet_to_pairs.py \
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

process EXTRACT_FEATURES {
    tag "extract-features"
    publishDir "${params.outdir}/features", mode: 'copy', pattern: 'features/**'
    publishDir "${params.outdir}/nuclei", mode: 'copy', pattern: 'nuclei/**', enabled: params.save_crops
    publishDir "${params.outdir}/logs", mode: 'copy', pattern: 'extract.log'

    input:
    tuple path(image_root), path(mat_root)

    output:
    path 'features', emit: features_dir
    path 'nuclei', emit: nuclei_dir, optional: true
    path 'features/**', emit: feature_files
    path 'nuclei/**', emit: nuclei_files, optional: true
    path 'extract.log', emit: extract_log

    script:
    def recursiveFlag = params.recursive ? '--recursive' : '--no-recursive'
    def useGpuFlag = params.use_gpu ? '--use-gpu' : '--no-use-gpu'
    def stainFlag = params.stain_normalization_features ? '--stain-normalization-features' : '--no-stain-normalization-features'
    def saveCropsFlag = params.save_crops ? '--save-crops' : '--no-save-crops'
    def savePreFlag = params.save_pre_normalized_crops ? '--save-pre-normalized-crops' : '--no-save-pre-normalized-crops'
    def savePostFlag = params.save_post_normalized_crops ? '--save-post-normalized-crops' : '--no-save-post-normalized-crops'
    def skipExistingFlag = params.skip_existing ? '--skip-existing' : ''
    def matKeyArg = params.mat_key ? "--mat-key ${params.mat_key}" : ''
    def maxImagesArg = params.max_images != null ? "--max-images ${params.max_images}" : ''

    """
    python -c "from nucxplore.batch import main as _main; raise SystemExit(_main())" \
      --image-root ${image_root} \
      --mat-root ${mat_root} \
      --output-csv-root features \
      --output-nuclei-root nuclei \
      --image-exts '${params.image_exts}' \
      --workers ${params.workers} \
      --inst-type-key '${params.inst_type_key}' \
      --padding ${params.padding} \
      ${recursiveFlag} \
      ${useGpuFlag} \
      ${stainFlag} \
      ${saveCropsFlag} \
      ${savePreFlag} \
      ${savePostFlag} \
      ${skipExistingFlag} \
      ${matKeyArg} \
      ${maxImagesArg} \
      > extract.log 2>&1
    """

    stub:
    """
    mkdir -p features nuclei
    printf 'nucleus_id,area\n1,10.0\n' > features/stub_features.csv
    : > extract.log
    """
}

process PREDICT_CELL_TYPES {
    tag "predict-cell-types"
    publishDir "${params.outdir}/predictions", mode: 'copy', pattern: 'predictions/**'
    publishDir "${params.outdir}/logs", mode: 'copy', pattern: 'manifest.json'
    publishDir "${params.outdir}/logs", mode: 'copy', pattern: 'manifest.csv'
    publishDir "${params.outdir}/logs", mode: 'copy', pattern: 'predict.log'

    input:
    path features_dir

    output:
    path 'predictions', emit: predictions_dir
    path 'predictions/**', emit: prediction_files, optional: true
    path 'manifest.json', emit: manifest_json
    path 'manifest.csv', emit: manifest_csv
    path 'predict.log', emit: predict_log

    script:
    """
    cell_type_predict.py \
      --input-features ${features_dir} \
      --output-dir predictions \
      --model ${params.model_path} \
      --encoder ${params.encoder_path} \
      --workers ${params.workers} \
      --manifest-json manifest.json \
      --manifest-csv manifest.csv \
      > predict.log 2>&1
    """

    stub:
    """
    mkdir -p predictions
    printf 'nucleus_id,Predicted_Label,Confidence_Score\n1,StubCell,1.0\n' > predictions/stub_predictions.csv
    printf '{"ok_files":1,"failed_files":0,"stub":true}\n' > manifest.json
    printf 'status,input_csv,output_csv,rows,error\nok,stub_features.csv,stub_predictions.csv,1,\n' > manifest.csv
    : > predict.log
    """
}

workflow {
    validateParams()
    fromIdx = stageIdx(params.from_stage)
    toIdx   = stageIdx(params.to_stage)

    // Channels populated by upstream stages (null / undefined until set).
    def imageRootCh
    def matRootCh

    // ==================== crop (idx 0) ====================
    if( fromIdx == 0 ) {
        slideCh = Channel.value(file(params.slide_root, checkIfExists: true))
        cropped_result = CROP_AND_FILTER(slideCh)
        if( toIdx == 0 ) { return }
        imageRootCh = cropped_result.cropped_dir
    }

    // ==================== segmentation (idx 1) ====================
    if( fromIdx <= 1 && toIdx >= 1 ) {
        if( fromIdx == 1 ) {
            cropCh = Channel.value(file(params.crop_root, checkIfExists: true))
            imageRootCh = cropCh
        }
        else {
            cropCh = cropped_result.cropped_dir
        }
        seg_result = RGCI_SEG(cropCh)
        matRootCh = seg_result.mats_dir
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
        // imageRootCh / matRootCh already set from upstream (crop/seg).
        extracted = EXTRACT_FEATURES(imageRootCh.combine(matRootCh))
        if( toIdx == 2 ) { return }
    }

    // ==================== prediction (idx 3) ====================
    if( fromIdx <= 3 && toIdx >= 3 ) {
        if( fromIdx == 3 ) {
            predInputCh = Channel.value(file(params.features_root, checkIfExists: true))
        }
        else {
            predInputCh = extracted.features_dir
        }
        PREDICT_CELL_TYPES(predInputCh)
        if( toIdx == 3 ) { return }
    }
}
